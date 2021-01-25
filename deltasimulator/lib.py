import asyncio
from os import path
from deltasimulator.build_tools import BuildArtifact, write
from deltasimulator.build_tools.environments import (PythonatorEnv,
                                                     VerilatorEnv,
                                                     WiringEnv,
                                                     CPPEnv,
                                                     HostEnv)
from capnp.lib.capnp import _DynamicStructBuilder

def generate_wiring(program: _DynamicStructBuilder) -> dict:
    """Creates the wiring of the nodes defined in a program.

    Parameters
    ----------
    program: _DynamicStructBuilder
        A Deltaflow serialized graph
    Returns
    -------
    node_bodies: list
        the bodies of the extracted nodes
    node_inits: list
        all the rom files found in the migen nodes, extracted as strings.
        This solves an incompatibility between some migen generated outputs
        and verilator.
    wiring: dict
        the wiring of the graph. This can be used to generate a SystemC top
        level to wire the graph
    """

    node_headers = []
    node_bodies = []
    node_modules = []
    node_objects = []
    node_inits = []
    verilated_o = None
    for node in program.nodes:
        if node.body != -1:
            # If node.body is -1 then it is a template node
            # and cannot be pythonated
            which_body = program.bodies[node.body].which()

            if which_body in ['python', 'interactive'] :
                with PythonatorEnv(program.bodies) as env:
                    build_artifacts = env.pythonate(node)
                    node_headers.append(build_artifacts["h"])
                    if "py" in build_artifacts:
                        node_bodies.append(build_artifacts["py"])
                    node_modules.append(build_artifacts["cpp"])
                    node_objects.append(build_artifacts["o"])

            elif which_body == 'migen':
                # This part is adopted from initial-example:
                top_v = BuildArtifact(name=f"{node.name}.v",
                                      data=program.bodies[node.body].migen.verilog.encode("utf8"))

                with VerilatorEnv() as env:
                    build_artifacts = env.verilate(top_v)

                node_headers.append(build_artifacts["h"])
                node_modules.append(build_artifacts["cpp"])
                node_objects.append(build_artifacts["ALL.a"])
                node_inits += build_artifacts["init"]
                if not verilated_o:
                    verilated_o = build_artifacts["verilated.o"]

    with WiringEnv(program.nodes,
                   program.bodies,
                   node_headers,
                   node_objects,
                   verilated_o,
                   program.name) as env:
        wiring = env.wiring(program.graph)

    return node_bodies, node_inits, wiring

async def _wait_for_build(wiring: dict):
    """Waits for all the objects associated with the wiring to be
    ready.

    Parameters
    ----------
    wiring
        A wired graph
    """

    for comp in wiring:
        _ = await asyncio.wait_for(wiring[comp].data, timeout=None)

def _copy_artifacts(main, inits, node_bodies, destination):
    """Copies all the required artifacts into a new destination

    Parameters
    ----------
    main
        the main file (main.cpp) for the graph
    inits
        the memory configuration files
    node_bodies
        the content of the nodes
    destination
        the folder to copy the artifacts into. Note: created if it does
        not exists
    """

    for init in inits:
        with open(path.join(destination, init.name), "wb") as f:
            write(init, f)

    for body in node_bodies:
        with open(path.join(destination, body.name), "wb") as f:
            write(body, f)

    with open(path.join(destination, "main"), "wb") as f:
        write(main, f)


def _compile_and_link(program_name: str, wiring: list, main_cpp: str):
    """Compiles and link the graph together with a provided top
    level file

    Parameters
    ----------
    program_name: str
        the name of the program to generate
    wiring: list
        a wired graph generated via cog
    main_cpp: str
        the top level main file
    """

    asyncio.run(_wait_for_build(wiring))
    _main_h = wiring[program_name + ".h"]
    _main_a = wiring[program_name + ".a"]
    # Converting the main.cpp into a BuildArtifact
    with HostEnv(dir=path.dirname(main_cpp)) as env:
        _main_cpp = BuildArtifact(name=path.basename(main_cpp), env=env)

    with CPPEnv() as cpp:
        main = cpp.compile_and_link(
            [_main_h],
            [_main_a],
            _main_cpp
        )
    return main


def build_graph(program: _DynamicStructBuilder, main_cpp: str, build_dir: str):
    """ Generates an executable to be stored in a build
    directory.

    Parameters
    ----------
    program: _DynamicStructBuilder
        The Deltaflow program to be converted into SystemC.
    main_cpp: str
        SystemC top level file that starts the SystemC simulation and
        defines an implementation for eventual templatedNodes.
    build_dir: str
        The target directory in which to store the output.

    Examples
    --------
    The *main.cpp* (other filenames are allowed) should at least contain the
    following:

    .. code-block:: c++

        #include <systemc>
        #include <Python.h>
        #include "dut.h"
        using namespace sc_dt;
        int sc_main(__attribute__(int argc, char** argv) {
            Py_UnbufferedStdioFlag = 1;
            Py_Initialize();
            sc_trace_file *Tf = nullptr;
            sc_clock clk("clk", sc_time(1, SC_NS));
            sc_signal<bool> rst;
            // Dut is the name you
            Dut dut("Dut", Tf);
            dut.clk.bind(clk);
            dut.rst.bind(rst);
            rst.write(0);
            sc_start(1000, SC_NS);
            return 0;
        }


    With the associate Python code:

    .. code-block:: python

        from deltalanguage.runtime import serialize_graph
        from deltasimulator.lib import build_graph
        ...
        _, program = serialize_graph(graph, name="dut")
        build_graph(program, main_cpp="main.cpp",
             build_dir="/workdir/build")
        ...

    .. todo::

        Setting stdio/stderr to not buffer is required because `Py_Finalize`
        can cause some memory errors (with eg the Qiskit HAL test).
        Is there a fix for this?

    """

    node_bodies, node_inits, wiring = generate_wiring(program)
    main = _compile_and_link(program.name, wiring, main_cpp)
    _copy_artifacts(main, node_inits, node_bodies, build_dir)
    for file in program.files:
        with open(path.join(build_dir, file.name), "wb") as support_file:
            support_file.write(file.content)


