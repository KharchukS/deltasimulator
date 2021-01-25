import os.path as path

import dill

from deltalanguage.wiring import PyConstBody

from .cppenv import CPPEnv
from .pythonator import PythonatorEnv
from .verilator import VerilatorEnv
from deltasimulator.build_tools import multiple_waits
from deltasimulator.build_tools.cogify import cogify
from deltasimulator.build_tools.fileio import BuildArtifact, write_futures


class WiringEnv(CPPEnv):
    """Environment that wires the completed graph together.

    When run, a .a archive is produced containing all built node objects,
    as well as a header file containing all node headers
    and a SystemC module for the wiring of nodes.

    If there are no template nodes in the graph then a main runtime is
    also produced and built into an executable. This can be run with
    either no arguments in which case the program runs until
    a :exc:`DeltaRuntimeExit` occurs, or with an optional integer argument
    in which case the program runs for the given number of nanoseconds.

    Parameters
    ----------
    capnp_nodes : list
        Nodes in the graph, described as capnp objects
    capnp_bodies : list
        Bodies for the nodes, described as capnp objects
    node_headers : list
        Header files for the nodes, wrapped in :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects.
    node_objects : list
        Built binary objects for the nodes.
        For Python nodes these are .o files, and for Migen these are .a
        archives. In both cases the files are wrapped in
        :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects.
    verilated_o : Optional[BuildArtifact]
        The content of the verilated.o file, which is required to link objects
        built using Verilator. Note that this is the same regardless of the
        node it was built with, so only a single copy is required.
    prog_name : Optional[str]
        The name of this program, by default "main"


    .. note::
        Connections are note made between pairs of constant Python nodes.
        This is because these nodes are evaluated during the build process
        and therefore require no input during runtime.

    .. note::
        For wiring up template nodes, the wires connecting to template
        nodes are exposed publicly so that these can be connected to their
        actual implementations. Note that connections between template nodes
        are not wired up, as we do not know the communication protocol
        between a pair of template nodes.

    .. note::
        Python nodes and Migen nodes have different communication protocols.
        The header file includes SystemC modules
        :cpp:class:`MigenToPython` and :cpp:class:`PythonToMigen` which
        convert between these different protocols. These can also be used
        to convert the signals between a node in the graph and the actual
        implementation of a template node if needed.
    """

    def __init__(self, capnp_nodes, capnp_bodies, node_headers, node_objects, verilated_o=None, prog_name="main"):
        super().__init__()
        if prog_name:
            self._prog_name = prog_name
        else:
            self._prog_name = "main"
        self._capnp_nodes = capnp_nodes
        self._capnp_bodies = capnp_bodies
        self._node_headers = node_headers
        self._node_objects = node_objects
        if verilated_o:
            self._node_objects.append(verilated_o)
        self._get_node_types()

    @staticmethod
    def get_wire_name(wire):
        """Gets the name of a wire.

        Parameters
        ----------
        wire
            capnp object describing a wire in the graph.

        Returns
        -------
        str
            The name of the wire used by this environment.
            The format used is `{src_node}_{src_port}_{dest_node}_{dest_port}`,
            where `src_node` & `dest_node` are the indexes of the source
            and destination node in the list of nodes, and `src_port`
            & `dest_port` are the indexes of the ports in their respective
            nodes list of ports.
        """
        return "_".join(["wire", str(wire.srcNode), str(wire.srcOutPort), str(wire.destNode), str(wire.destInPort)])

    def get_template_wire_name(self, wire, body="python", direction="out"):
        """Gets standardised name of a wire connecting to a template node.

        These names are a different formats as they are public, so the name
        is more human-readable.

        Parameters
        ----------
        wire
            capnp object describing a wire in the graph.
        body : Optional[str]
            The body-type of the non-template node, by default "python"
        direction : Optional[str]
            The direction of the wire, by default "out"

        Returns
        -------
        str
            The name of the wire used by this environment.
            The format used is `{node_name}_{wire_name}` where
            `node_name` is the name of the node and `wire_name` is the
            name of the SystemC module's port.
            See :meth:`PythonatorEnv.get_sysc_port_name` and
            :meth:`VerilatorEnv.get_sysc_port_name` for the formats of
            `wire_name`.
        """
        if direction == "out":
            node = self._capnp_nodes[wire.srcNode]
            port = node.outPorts[wire.srcOutPort]
        elif direction == "in":
            node = self._capnp_nodes[wire.destNode]
            port = node.inPorts[wire.destInPort]
        if body == "python":
            return f"{node.name}_{PythonatorEnv.get_sysc_port_name(port)}"
        elif body == "interactive":
            return f"{node.name}_{PythonatorEnv.get_sysc_port_name(port)}"
        elif body == "migen":
            return (f"{node.name}_{wire_name}" for wire_name in VerilatorEnv.get_sysc_port_name(port, direction=direction))

    def _get_top_name(self):
        """Gets name of top module.

        Returns
        -------
        str
            The name of the module. The format is a capitalised version
            of the program's name.
        """
        return "_".join([word.capitalize() for word in self._prog_name.split("_")])

    def _get_node_types(self):
        """Determines which nodes are python, migen or template"""
        self._py_nodes = []
        self._migen_nodes = []
        self._has_templates = False
        for node in self._capnp_nodes:
            if node.body == -1:
                self._has_templates = True
            else:
                body_type = self._capnp_bodies[node.body].which()
                if body_type in ["python", "interactive"]:
                    self._py_nodes.append(node)
                elif body_type == "migen":
                    self._migen_nodes.append(node)

    def _get_adaptors(self, capnp_graph):
        """Determines which conversions are needed between nodes"""
        self._py_to_py = []
        self._py_to_migen = []
        self._py_to_template = []
        self._migen_to_migen = []
        self._migen_to_py = []
        self._migen_to_template = []
        self._template_to_py = []
        self._template_to_migen = []
        num_const_wires = 0
        for wire in capnp_graph:
            src_body_index = self._capnp_nodes[wire.srcNode].body
            if (src_body_index == -1):
                src_body_type = "template"
            else:
                src_body_type = self._capnp_bodies[src_body_index].which()
            dest_body_index = self._capnp_nodes[wire.destNode].body
            if (dest_body_index == -1):
                dest_body_type = "template"
            else:
                dest_body_type = self._capnp_bodies[dest_body_index].which()
            if (src_body_type in ["python", "interactive"]) and (dest_body_type in ["python", "interactive"]):
                if src_body_type == "interactive":
                    src_body = type(dill.loads(self._capnp_bodies[src_body_index].interactive.dillImpl))
                else:
                    src_body = type(dill.loads(self._capnp_bodies[src_body_index].python.dillImpl))
                if dest_body_type == "interactive":
                    dest_body = type(dill.loads(self._capnp_bodies[dest_body_index].interactive.dillImpl))
                else:
                    dest_body = type(dill.loads(self._capnp_bodies[dest_body_index].python.dillImpl))
                if (src_body is PyConstBody) and (dest_body is PyConstBody):
                    # Don't wire constant-to-constant nodes
                    num_const_wires += 1
                else:
                    self._py_to_py.append(wire)
            elif (src_body_type in ["python", "interactive"]) and (dest_body_type == "migen"):
                self._py_to_migen.append(wire)
            elif (src_body_type in ["python", "interactive"]) and (dest_body_type == "template"):
                self._py_to_template.append(wire)
            elif (src_body_type == "migen") and (dest_body_type == "migen"):
                self._migen_to_migen.append(wire)
            elif (src_body_type == "migen") and (dest_body_type in ["python", "interactive"]):
                self._migen_to_py.append(wire)
            elif (src_body_type == "migen") and (dest_body_type == "template"):
                self._migen_to_template.append(wire)
            elif (src_body_type == "template") and (dest_body_type in ["python", "interactive"]):
                self._template_to_py.append(wire)
            elif (src_body_type == "template") and (dest_body_type == "migen"):
                self._template_to_migen.append(wire)
        if num_const_wires == len(capnp_graph) and num_const_wires > 0:
            raise RuntimeError("Graph cannot consist of only constant nodes.")

    async def _make_main(self):
        """Makes the C++ file containing :cpp:func:`sc_main`.

        Returns
        -------
        bool
            Returns True when complete.


        .. warning::
            Only run this method if there are no template nodes in the graph.
            Otherwise the graph will be incomplete and fail to run correctly.
        """
        main_tmpl = """
        #include <systemc>
        #include <iostream>
        #include <string>
        /*[[[cog
            cog.outl(f'#include "{self._prog_name}.h"')
        ]]]*/
        //[[[end]]]
        #include "Python.h"
        using namespace sc_core;
        using namespace std;
        int sc_main(int argc, char* argv[]) {
            Py_UnbufferedStdioFlag = 1;
            Py_Initialize();
            // Adds required components: trace, clock, reset
            /*[[[cog
                cog.outl(f'sc_trace_file *Tf = sc_create_vcd_trace_file("{self._prog_name}");')
                cog.outl(f'{self._get_top_name()} {self._prog_name}("{self._prog_name}", Tf);')
                cog.outl(f'sc_clock clk("clk", sc_time(1, SC_NS)); sc_trace(Tf, clk, "clk");')
                cog.outl(f'sc_signal<bool> rst; sc_trace(Tf, rst, "rst");')
            ]]]*/
            //[[[end]]]
            rst.write(0);
            /*[[[cog
                cog.outl(f'{self._prog_name}.clk.bind(clk);')
                cog.outl(f'{self._prog_name}.rst.bind(rst);')
            ]]]*/
            //[[[end]]]

            /* Flush the simulation to start with, then run if
            the program hasn't already terminated.
            If a timeout argument has been passed in then run for that many
            nanoseconds. */
            rst.write(1);
            sc_start(5, SC_NS);
            rst.write(0);
            try {
                if (!sc_end_of_simulation_invoked()) {
                    if (argc > 1) sc_start(atoi(argv[1]), SC_NS);
                    else sc_start();
                }
                cout << "exiting on timeout" << endl;
                sc_close_vcd_trace_file(Tf);
            } catch (...) {
                cout << "exiting on error" << endl;
                sc_close_vcd_trace_file(Tf);
                throw;
            }

            std::cout << "exiting normally" << std::endl;
            return 0;
        }
        """
        with open(path.join(self.tempdir, f"{self._prog_name}.cpp"), "wb") as main_path:
            main_path.write(cogify(main_tmpl, globals=locals()))
        return True

    def _get_main_cpp(self, after):
        """Gets the main runtime's C++ file.

        Parameters
        ----------
        after : Coroutine
            Process which builds the C++ file.

        Returns
        -------
        BuildArtifact
            The C++ code containing :cpp:func:`sc_main`.
        """
        return BuildArtifact(f"{self._prog_name}.cpp", self, after=after)

    async def _make_top(self):
        """Makes the top module, where the wiring is defined.
        The top header also contains all node module definitions
        and the converters from Python to Migen nodes.

        Returns
        -------
        bool
            Returns True when completed.
        """
        top_tmpl = """
        /*[[[cog
            cog.outl(f'#ifndef __{self._prog_name.upper()}__')
            cog.outl(f'#define __{self._prog_name.upper()}__')
        ]]]*/
        //[[[end]]]
        #include <systemc>
        using namespace sc_core;
        using namespace sc_dt;

        // TODO: Find better way of handling trace files
        sc_trace_file *Tf;

        // Converts clock signals to bit vectors for Migen nodes
        SC_MODULE(ClkToBV) {
            sc_in<bool> clk;
            sc_out<sc_bv<1>> clkout;

            void run() {
                clkout.write(clk.read());
            }

            SC_CTOR(ClkToBV) {
                SC_METHOD(run);
                sensitive << clk;
            }
        };

        // Adaptor for going from Python to Migen
        template <class T> SC_MODULE(PythonToMigen) {
            sc_in<bool> clk;
            sc_out<T> migen_data_out;
            sc_out<sc_bv<1>> migen_valid_out;
            sc_in<sc_bv<1>> migen_ready_in;
            sc_fifo<T>* py_in;

            void run() {
                if (migen_ready_in.read() == 1) {
                    T val;
                    if (py_in->nb_read(val)) {
                        migen_data_out.write(val);
                        migen_valid_out.write(1);
                    } else {
                        migen_valid_out.write(0);
                    }
                }
            }

            SC_CTOR(PythonToMigen) {
                SC_METHOD(run);
                sensitive << clk.pos();
            }
        };

        // Adaptor for going from Migen to Python
        template <class T> SC_MODULE(MigenToPython) {
            sc_in<bool> clk;
            sc_in<T> migen_in;
            sc_in<sc_bv<1>> migen_valid_in;
            sc_out<sc_bv<1>> migen_ready_out;
            sc_fifo<T>* py_out;

            void run() {
                while (true) {
                    wait();
                    if (py_out->num_free() > 0) {
                        migen_ready_out.write(1);
                        if (migen_valid_in.read() == 1) {
                            py_out->write(migen_in.read());
                        }
                    } else {
                        migen_ready_out.write(0);
                    }
                }
            }

            SC_CTOR(MigenToPython) {
                SC_THREAD(run);
                sensitive << clk.pos();
            }
        };

        /*[[[cog
            cog.outl(f'SC_MODULE({self._get_top_name()}){{')
        ]]]*/
        //[[[end]]]

        // Python nodes to Python nodes just need a queue
        /*[[[cog
            for wire in self._py_to_py:
                name = self.get_wire_name(wire)
                cog.outl(f'sc_fifo<{PythonatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name};')
        ]]]*/
        //[[[end]]]

        // Migen nodes to Migen nodes need data wires,
        // as well as valid and ready signals
        /*[[[cog
            for wire in self._migen_to_migen:
                name = self.get_wire_name(wire)
                cog.outl(f'sc_signal<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_data;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_valid;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_ready;')
        ]]]*/
        //[[[end]]]

        // Python to Migen need an adaptor which maps a queue
        // to data, valid and ready signals.
        /*[[[cog
            for wire in self._py_to_migen:
                name = self.get_wire_name(wire)
                cog.outl(f'sc_fifo<{PythonatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_py_out;')
                cog.outl(f'sc_signal<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_migen_in;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_in_valid;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_in_ready;')
                cog.outl(f'PythonToMigen<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_adaptor;')
        ]]]*/
        //[[[end]]]

        // Migen to Python need an adaptor which maps signals
        // to a queue
        /*[[[cog
            for wire in self._migen_to_py:
                name = self.get_wire_name(wire)
                cog.outl(f'sc_fifo<{PythonatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_py_in;')
                cog.outl(f'sc_signal<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_migen_out;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_out_valid;')
                cog.outl(f'sc_signal<sc_bv<1>> {name}_out_ready;')
                cog.outl(f'MigenToPython<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name}_adaptor;')
        ]]]*/
        //[[[end]]]

        // Python to template need a public queue
        /*[[[cog
            for wire in self._py_to_template:
                name = self.get_template_wire_name(wire, body="python", direction="out")
                cog.outl(f'sc_fifo<{PythonatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name};')
        ]]]*/
        //[[[end]]]

        // Template to python need a public queue
        /*[[[cog
            for wire in self._template_to_py:
                name = self.get_template_wire_name(wire, body="python", direction="in")
                cog.outl(f'sc_fifo<{PythonatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {name};')
        ]]]*/
        //[[[end]]]

        // Migen to template need public data, valid and ready signals
        /*[[[cog
            for wire in self._migen_to_template:
                data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="out")
                cog.outl(f'sc_signal<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {data};')
                cog.outl(f'sc_signal<sc_bv<1>> {valid};')
                cog.outl(f'sc_signal<sc_bv<1>> {ready};')
        ]]]*/
        //[[[end]]]

        // Template to Migen need public data, valid and ready signals
        /*[[[cog
            for wire in self._template_to_migen:
                data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="in")
                cog.outl(f'sc_signal<{VerilatorEnv.as_c_type(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort].type)}> {data};')
                cog.outl(f'sc_signal<sc_bv<1>> {valid};')
                cog.outl(f'sc_signal<sc_bv<1>> {ready};')
        ]]]*/
        //[[[end]]]

        sc_in<bool> clk, rst;
        sc_signal<sc_dt::sc_bv<1>> rst_bv;

        // Node modules
        /*[[[cog
            for node in self._py_nodes:
                cog.outl(f'{PythonatorEnv.get_module_name(node)} {node.name};')
        ]]]*/
        //[[[end]]]

        /*[[[cog
            for node in self._migen_nodes:
                cog.outl(f'{VerilatorEnv.get_module_name(node)} {node.name};')
                cog.outl(f'ClkToBV {node.name}_clk;')
                cog.outl(f'sc_signal<sc_bv<1>> {node.name}_sysclk;')
        ]]]*/
        //[[[end]]]

        // Constructor first initialises queues, modules and adaptors
        /*[[[cog
            cog.outl(f'typedef {self._get_top_name()} SC_CURRENT_USER_MODULE;')
            cog.outl(f'{self._get_top_name()}(sc_module_name name, sc_trace_file *Tf):')

            init_modules = []
            for wire in self._py_to_py:
                init_modules.append(f'{self.get_wire_name(wire)}("{self.get_wire_name(wire)}")')

            for wire in self._py_to_migen:
                name = self.get_wire_name(wire)
                init_modules.append(f'{name}_py_out("{name}_py_out")')
                init_modules.append(f'{name}_adaptor("{name}_adaptor")')

            for wire in self._migen_to_py:
                name = self.get_wire_name(wire)
                init_modules.append(f'{name}_py_in("{name}_py_in")')
                init_modules.append(f'{name}_adaptor("{name}_adaptor")')

            for node in self._py_nodes:
                init_modules.append(f'{node.name}("{node.name}")')

            for node in self._migen_nodes:
                init_modules.append(f'{node.name}("{node.name}")')
                init_modules.append(f'{node.name}_clk("{node.name}_clk")')

            cog.out(",\\n".join(init_modules))
        ]]]*/
        //[[[end]]]
        {
            SC_METHOD(rstprop);
            sensitive << rst;

            // Wiring the clock to the Migen nodes
            /*[[[cog
                for node in self._migen_nodes:
                    cog.outl(f'{node.name}_clk.clk(clk);')
                    cog.outl(f'{node.name}_clk.clkout.bind({node.name}_sysclk);')
                    cog.outl(f'{node.name}.sys_clk.bind({node.name}_sysclk);')
                    cog.outl(f'sc_trace(Tf, {node.name}_sysclk, \"{node.name}_sysclk\");')
                    cog.outl(f'{node.name}.sys_rst.bind(rst_bv);')
            ]]]*/
            //[[[end]]]

            // Wiring the Python to Python nodes
            /*[[[cog
                for wire in self._py_to_py:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort])} = &{name};')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort])} = &{name};')
            ]]]*/
            //[[[end]]]

            // Wiring the Migen to Migen nodes
            /*[[[cog
                for wire in self._migen_to_migen:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({name}_data);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({name}_data);')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({name}_valid);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({name}_valid);')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="in")}.bind({name}_ready);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="out")}.bind({name}_ready);')
            ]]]*/
            //[[[end]]]

            // Wiring the Python to Migen nodes
            /*[[[cog
                for wire in self._py_to_migen:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort])} = &{name}_py_out;')
                    cog.outl(f'{name}_adaptor.clk(clk);')
                    cog.outl(f'{name}_adaptor.py_in = &{name}_py_out;')
                    cog.outl(f'{name}_adaptor.migen_data_out.bind({name}_migen_in);')
                    cog.outl(f'{name}_adaptor.migen_valid_out.bind({name}_in_valid);')
                    cog.outl(f'{name}_adaptor.migen_ready_in.bind({name}_in_ready);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({name}_migen_in);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({name}_in_valid);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="out")}.bind({name}_in_ready);')
            ]]]*/
            //[[[end]]]

            // Wiring the Migen to Python nodes
            /*[[[cog
                for wire in self._migen_to_py:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{name}_adaptor.clk(clk);')
                    cog.outl(f'{name}_adaptor.migen_in.bind({name}_migen_out);')
                    cog.outl(f'{name}_adaptor.migen_valid_in.bind({name}_out_valid);')
                    cog.outl(f'{name}_adaptor.migen_ready_out.bind({name}_out_ready);')
                    cog.outl(f'{name}_adaptor.py_out = &{self.get_wire_name(wire)}_py_in;')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({name}_migen_out);')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({name}_out_valid);')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="in")}.bind({name}_out_ready);')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort])} = &{name}_py_in;')
            ]]]*/
            //[[[end]]]

            // Wiring the Python to template nodes
            /*[[[cog
                for wire in self._py_to_template:
                    name = self.get_template_wire_name(wire, body="python", direction="out")
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort])} = &{name};')
            ]]]*/
            //[[[end]]]

            // Wiring the template to Python nodes
            /*[[[cog
                for wire in self._template_to_py:
                    name = self.get_template_wire_name(wire, body="python", direction="in")
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{PythonatorEnv.get_sysc_port_name(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort])} = &{name};')
            ]]]*/
            //[[[end]]]

            // Wiring the Migen to template nodes
            /*[[[cog
                for wire in self._migen_to_template:
                    data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="out")
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({data});')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="out")}.bind({valid});')
                    cog.outl(f'{self._capnp_nodes[wire.srcNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.srcNode].outPorts[wire.srcOutPort], direction="in")}.bind({ready});')
            ]]]*/
            //[[[end]]]

            // Wiring the template to Migen nodes
            /*[[[cog
                for wire in self._template_to_migen:
                    data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="in")
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_output(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({data});')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_valid(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="in")}.bind({valid});')
                    cog.outl(f'{self._capnp_nodes[wire.destNode].name}.{VerilatorEnv.get_port_ready(self._capnp_nodes[wire.destNode].inPorts[wire.destInPort], direction="out")}.bind({ready});')
            ]]]*/
            //[[[end]]]

            // Add tracing
            /*[[[cog
                for wire in self._py_to_py:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{name}.trace(Tf);')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._migen_to_migen:
                    name = self.get_wire_name(wire)
                    cog.outl(f'sc_trace(Tf, {name}_data, "{name}_data");')
                    cog.outl(f'sc_trace(Tf, {name}_valid, "{name}_valid");')
                    cog.outl(f'sc_trace(Tf, {name}_ready, "{name}_ready");')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._py_to_migen:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{name}_py_out.trace(Tf);')
                    cog.outl(f'sc_trace(Tf, {name}_migen_in, "{name}_migen_in");')
                    cog.outl(f'sc_trace(Tf, {name}_in_valid, "{name}_in_valid");')
                    cog.outl(f'sc_trace(Tf, {name}_in_ready, "{name}_in_ready");')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._migen_to_py:
                    name = self.get_wire_name(wire)
                    cog.outl(f'{name}_py_in.trace(Tf);')
                    cog.outl(f'sc_trace(Tf, {name}_migen_out, "{name}_migen_out");')
                    cog.outl(f'sc_trace(Tf, {name}_out_valid, "{name}_out_valid");')
                    cog.outl(f'sc_trace(Tf, {name}_out_ready, "{name}_out_ready");')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._py_to_template:
                    name = self.get_template_wire_name(wire, 'python', 'out')
                    cog.outl(f'{name}.trace(Tf);')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._template_to_py:
                    name = self.get_template_wire_name(wire, 'python', 'in')
                    cog.outl(f'{name}.trace(Tf);')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._migen_to_template:
                    data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="out")
                    cog.outl(f'sc_trace(Tf, {data}, "{data}");')
                    cog.outl(f'sc_trace(Tf, {valid}, "{valid}");')
                    cog.outl(f'sc_trace(Tf, {ready}, "{ready}");')
            ]]]*/
            //[[[end]]]

            /*[[[cog
                for wire in self._template_to_migen:
                    data, valid, ready = self.get_template_wire_name(wire, body="migen", direction="in")
                    cog.outl(f'sc_trace(Tf, {data}, "{data}");')
                    cog.outl(f'sc_trace(Tf, {valid}, "{valid}");')
                    cog.outl(f'sc_trace(Tf, {ready}, "{ready}");')
            ]]]*/
            //[[[end]]]
        }

        void rstprop() {
            // Propogate reset signal to Migen nodes
            rst_bv.write(rst.read());
        }

        };

        #endif
        """

        with open(path.join(self.tempdir, f"{self._prog_name}.h"), "wb") as top_path:
            await multiple_waits([write_futures(header, top_path) for header in self._node_headers])
            top_path.write(cogify(top_tmpl, globals=dict(globals(), **locals())))
        return True

    def _get_top_h(self, after):
        """Get the top header file.

        Parameters
        ----------
        after : Coroutine
            Process which builds the header file.

        Returns
        -------
        BuildArtifact
            The top header file.
        """
        return BuildArtifact(f"{self._prog_name}.h", self, after=after)

    async def _build_main(self, after):
        """Builds the main.o binary object containing the
        :cpp:func:`sc_main` runtime

        Parameters
        ----------
        after : Coroutine
            The process which builds the main runtime's C++ file.

        Returns
        -------
        bool
            Returns True when complete.
        """
        done = await self._run_gcc(f"{self._prog_name}", after)
        return done

    def _get_main_object(self, after):
        """Get the binary object conatining sc_main.

        Parameters
        ----------
        after : Coroutine
            Process which builds the binary object.

        Returns
        -------
        BuildArtifact
            The :cpp:func:`sc_main` binary object.
        """
        return BuildArtifact(f"{self._prog_name}.o", self, after=after)

    async def _write_objects(self):
        """Writes all objects in to the temporary directory.

        Returns
        -------
        bool
            Returns True when complete.
        """
        object_paths = [open(path.join(self.tempdir, module.name), "wb") for module in self._node_objects]
        await multiple_waits([write_futures(module, object_path) for module, object_path in zip(self._node_objects, object_paths)])
        for object_path in object_paths:
            object_path.close()
        return True

    async def _make_archive(self, after):
        """Run ar to compile a .a archive containing the
        binary objects for all nodes.

        Parameters
        ----------
        after : list
            :class:`Coroutine` objects which writes the objects to
            the environment's temporary directory.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        done = await self._run_ar([object_file.name for object_file in self._node_objects], after=after, name=self._prog_name)
        return done

    async def _link_objects(self, main_o, archive, after):
        """Links sc_main binary object with all other objects
        to create a complete runtime.

        Parameters
        ----------
        main_o : BuildArtifact
            The binary object containing the :cpp:func:`sc_main` runtime.
        archive : BuildArtifact
            The .a archive containing all other objects.
        after : list
            Coroutines for building the main object and archive.

        Returns
        -------
        bool
            Returns True when complete.
        """
        done = await self._link(main_o.name, archive, after=after, name=self._prog_name)
        return done

    def wiring(self, capnp_graph):
        """Wire the full graph together and return the complete build.

        Parameters
        ----------
        capnp_graph
            capnp object describing the full wiring

        Returns
        -------
        dict
            Map from strings to :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects.
            Mapping is the following, where `prog_name` is the name of
            the program:

            - "{prog_name}.h": the header file containing all node headers and the full wiring module.
            - "{prog_name}.a": .a archive containing all built objects.

            If there are no template nodes the following are also provided:

            - "{prog_name}.cpp": C++ code containing :cpp:func:`sc_main` for complete runtime
            - "{prog_name}.o" binary object for :cpp:func:`sc_main`
            - "{prog_name}" complete runtime executable.

        """
        self._get_adaptors(capnp_graph)
        make_top = self._make_top()
        top_h = self._get_top_h(make_top)
        if not self._has_templates:
            make_main = self._make_main()
            main_file = self._get_main_cpp(make_main)
            build_main = self._build_main([make_main, make_top])
            main_o = self._get_main_object(build_main)
        write_objects = self._write_objects()
        make_archive = self._make_archive([write_objects])
        main_a = self._get_archive(make_archive, name=self._prog_name)
        if not self._has_templates:
            link_objects = self._link_objects(main_o, main_a, [build_main, make_archive])
            complete_runtime = self._get_main(link_objects, name=self._prog_name)
        build_artifacts = dict()
        build_artifacts[f"{self._prog_name}.h"] = top_h
        build_artifacts[f"{self._prog_name}.a"] = main_a
        if not self._has_templates:
            build_artifacts[f"{self._prog_name}.cpp"] = main_file
            build_artifacts[f"{self._prog_name}.o"] = main_o
            build_artifacts[f"{self._prog_name}"] = complete_runtime
        return build_artifacts
