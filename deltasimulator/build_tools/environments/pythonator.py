import asyncio
from io import StringIO
from os import path
import re
import sysconfig
import textwrap

import dill

from deltalanguage.runtime import DeltaRuntimeExit
from deltalanguage.wiring import PyConstBody, PyInteractiveBody

from .cppenv import CPPEnv
from deltasimulator.build_tools import BuildArtifact, cogify
from deltasimulator.build_tools.utils import multiple_waits

indent_prefix = "    "


class PythonatorEnv(CPPEnv):
    """Environment for generating SystemC modules of Python nodes.

    :py:meth:`cogify` is used to automatically generate the Python, C++ and
    header files.

    Parameters
    ----------
    bodies : list
        List of the node bodies, as stored in capnp format.


    .. note::
        Python nodes communicate to each other via SystemC FIFO queues.
        Each queue can store up to 16 items on it. If a node tries to push
        to an already full queue it will be blocked. Similarly, if a node
        tries to read from an empty queue it will be blocked, unless the
        input is optional in which case the node will receive `None`.

    .. note::
        As well as their C++ and header files, a Python script is also
        produced containing the body and data types for the node. This script
        must be stored in the working directory, in order for the nodes to
        load correctly.

    .. note::
        Constant nodes function differently to other Python nodes. Rather
        than evaluating their bodies at runtime, their bodies are evaluated
        as part of the build process and the result hardcoded into the
        output ports. As a result, these nodes do not receive any input and
        have no accompanying Python script.
    """

    def __init__(self, bodies):
        """Initialise the environment

        Parameters
        ----------
        bodies : List[Body]
            List of the node bodies
        """
        super().__init__()
        self._bodies = bodies

    @staticmethod
    def load_port_type(port):
        return dill.loads(port.type)

    @staticmethod
    def as_c_type(df_type):
        """Convert a Deltaflow type to a C type.

        Parameters
        ----------
        df_type : bytes
            The dill serialisation of the Deltaflow type.

        Returns
        -------
        str
            A string describing the SystemC equivalent.
            The format of the string is `sc_dt::sc_bv<{size}>`,
            where `size` is the size of the data type in bits.
        """
        return f"sc_dt::sc_bv<{dill.loads(df_type).size}>"

    @staticmethod
    def get_sysc_port_name(port):
        """Get the name of this port as a SystemC variable.

        Parameters
        ----------
        port
            ``capnp`` object describing the port.

        Returns
        -------
        str
            The name of this port in the SystemC module.
            The format used is `sysc_{port_name}`, where
            `port_name` is the name of the port.
        """
        if port.name:
            return f"sysc_{port.name}"
        else:
            raise ValueError("No name on port")

    @staticmethod
    def get_module_name(top_p):
        """Get the name of the node's SystemC module.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.

        Returns
        -------
        str
            The name of the node's module.
            The format used is `{Node_Name}_module`, where
            `Node_Name` is the capitalised version of the name of the node.
        """
        return "_".join([word.capitalize() for word in top_p.name.split("_")])\
            + "_module"

    async def _make_py(self, top_p, df_body, body_type):
        """Makes Python script for the node.

        The Python script contains the node's body as well as data types
        for input and output ports.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.

        Returns
        -------
        bool
            Returns True on completion.
        """

        body_file = path.join(self.tempdir, f"{top_p.name}.py")
        module_name = self.get_module_name(top_p)

        py_tmpl = "\nimport dill\n"

        if body_type is PyInteractiveBody:
            py_tmpl += f"import {module_name.lower()}_sysc\n"

        py_tmpl += f"body = dill.loads({df_body})\n"
        for port in top_p.inPorts:
            py_tmpl += f"{self.get_sysc_port_name(port)} = dill.loads({port.type})\n"
        for port in top_p.outPorts:
            py_tmpl += f"{self.get_sysc_port_name(port)} = dill.loads({port.type})\n"
        if body_type is PyInteractiveBody:
            py_tmpl += f"class SysBridgeNode:\n"
            inports_list = []
            if len(top_p.inPorts) > 0:
                py_tmpl += textwrap.indent(f"def __init__(self):\n", indent_prefix)
                for port in top_p.inPorts:
                    inports_list.append(port.name)
                inports_str = '[' + '"{0}"'.format('", "'.join(inports_list)) + ']'
                if (len(inports_list) > 0):
                    py_tmpl += textwrap.indent(
                        f"self.in_queues = dict.fromkeys({inports_str})\n",
                        indent_prefix * 2
                    )
            send_args_str = 'self' + ''.join(
                ', ' + port.name + '=None' for port in top_p.outPorts
            )
            py_tmpl += textwrap.indent(
                f"def send({send_args_str}):\n", indent_prefix
            )
            for port in top_p.outPorts:
                py_tmpl += textwrap.indent(
                    f"if {port.name} is not None:\n", indent_prefix * 2
                )
                py_tmpl += textwrap.indent(
                    f"{module_name.lower()}_sysc.send(\"{port.name}\", " +
                    f"{self.get_sysc_port_name(port)}.pack({port.name}))\n",
                    indent_prefix * 3
                )
            py_tmpl += textwrap.indent(
                f"def receive(self, *args: str):\n", indent_prefix
            )
            if (len(inports_list) == 0):
                py_tmpl += textwrap.indent(
                    f"raise RuntimeError\n", indent_prefix * 2
                )
            py_tmpl += textwrap.indent(f"if args:\n", indent_prefix * 2)
            py_tmpl += textwrap.indent(
                "in_queue = {name: in_q for name, in_q in self.in_queues.items() if name in args}\n",
                indent_prefix * 3
            )
            py_tmpl += textwrap.indent(f"else:\n", indent_prefix * 2)
            py_tmpl += textwrap.indent(
                f"in_queue = self.in_queues\n", indent_prefix * 3
            )
            py_tmpl += textwrap.indent("values = {}\n", indent_prefix * 2)
            py_tmpl += textwrap.indent(f"if in_queue:\n", indent_prefix * 2)
            py_tmpl += textwrap.indent(
                f"for req in in_queue:\n", indent_prefix * 3
            )
            py_tmpl += textwrap.indent(
                f"values[req] = {module_name.lower()}_sysc.receive(req)\n",
                indent_prefix * 4
            )
            py_tmpl += textwrap.indent(
                f"if len(values) == 1 and args:\n", indent_prefix * 2
            )
            py_tmpl += textwrap.indent(
                f"return values[list(values)[0]]\n", indent_prefix * 3
            )
            py_tmpl += textwrap.indent(f"else:\n", indent_prefix * 2)
            py_tmpl += textwrap.indent(f"return values\n", indent_prefix * 3)
            py_tmpl += f"node = SysBridgeNode()\n"

        with open(body_file, "w") as py_file:
            py_file.write(py_tmpl)
        return True

    def _get_py(self, top_p, after):
        """Get the node's Python script.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.
        after : Coroutine
            Process that needs to complete before the Python script is ready.

        Returns
        -------
        BuildArtifact
            The Python script for this node.
        """
        return BuildArtifact(f"{top_p.name}.py", self, after=after)

    async def _make_h(self, top_p,
                      body_type  # pylint: disable=unused-argument
                      ):
        """Generate the Header file for this node.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.
        body_type
            The type of body this node has. Used to check if the node is a
            constant node or not.

        Returns
        -------
        bool
            Returns True upon completion.
        """

        module_name = self.get_module_name(top_p)
        h_name = path.join(self.tempdir, f"{top_p.name}.h")

        h_tmpl = f"#ifndef __{top_p.name.upper()}_MODULE__\n"
        h_tmpl += f"#define __{top_p.name.upper()}_MODULE__\n\n"

        h_tmpl += f"#include <string>\n"
        h_tmpl += f"#include <systemc>\n"
        h_tmpl += f"using namespace sc_core;\n"

        if body_type is not PyConstBody:
            h_tmpl += '#include "Python.h"\n'

        h_tmpl += f"\nclass {module_name} : public sc_module\n"
        h_tmpl += "{\nprivate:\n"

        h_tmpl_ind = ""

        if body_type is not PyConstBody:
            h_tmpl_ind += "PyObject *pBody, *pName, *pModule, *pyC, *pExit;\n"
        if body_type is PyInteractiveBody:
            h_tmpl_ind += "PyObject *runtimeModule, *pNode;\n"
            h_tmpl_ind += "static PyObject* sc_receive(PyObject *self, PyObject *args);\n"
            h_tmpl_ind += "static PyObject* sc_send(PyObject *self, PyObject *args);\n"
            h_tmpl_ind += "static PyObject* PyInit_sysc(void);\n"
            h_tmpl_ind += "static PyMethodDef SysCMethods[];\n"
            h_tmpl_ind += "static PyModuleDef SysCModule;\n"
            h_tmpl_ind += f"static {module_name}* singleton;\n"
            h_tmpl_ind += "void init();\n"
            h_tmpl_ind += "void store();\n"
            h_tmpl_ind += "void run();\n"

        h_tmpl_ind += "uint64_t no_ins, no_outs;\n"

        if body_type is not PyConstBody:
            for port in top_p.inPorts:
                h_tmpl_ind += f"PyObject* type_{self.get_sysc_port_name(port)};\n"
                h_tmpl_ind += f"PyObject* get_{self.get_sysc_port_name(port)}();\n"
                h_tmpl_ind += f"{self.as_c_type(port.type)} bits_{self.get_sysc_port_name(port)};\n"
        for port in top_p.outPorts:
            if body_type is not PyConstBody:
                h_tmpl_ind += f"PyObject* type_{self.get_sysc_port_name(port)};\n"
                h_tmpl_ind += f"{self.as_c_type(port.type)} bits_{self.get_sysc_port_name(port)};\n"
            h_tmpl_ind += f"void set_{self.get_sysc_port_name(port)}();\n"

        h_tmpl += textwrap.indent(h_tmpl_ind, indent_prefix) + "public:\n"
        h_tmpl_ind = "uint64_t no_inputs, no_outputs;\n"
        if body_type is not PyConstBody:
            for port in top_p.inPorts:
                h_tmpl_ind += f"sc_fifo<{self.as_c_type(port.type)}>* {self.get_sysc_port_name(port)};\n"
        for port in top_p.outPorts:
            h_tmpl_ind += f"sc_fifo<{self.as_c_type(port.type)}>* {self.get_sysc_port_name(port)};\n"

        h_tmpl_ind += "int get_no_inputs() const;\n"
        h_tmpl_ind += "int get_no_outputs() const;\n"
        h_tmpl_ind += "void body();\n"
        h_tmpl_ind += f"SC_HAS_PROCESS({module_name});\n"
        h_tmpl_ind += f"{module_name}(sc_module_name name);\n"
        h_tmpl += textwrap.indent(h_tmpl_ind, indent_prefix) + "};\n#endif\n"

        with open(h_name, "w") as out_file:
            out_file.write(h_tmpl)
        return True

    def _get_h(self, top_p, after):
        """Get the Header file for the node.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.
        after : Coroutine
            The process that constructs the Header file.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        return BuildArtifact(f"{top_p.name}.h", self, after=after)

    async def _make_cpp(self, top_p,
                        body_type,  # pylint: disable=unused-argument
                        body_id
                        ):
        """Construct the node's SystemC module.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.
        body_type
            The type of body this node has. Used to check if the node is a
            constant node or not.

        Returns
        -------
        bool
            Returns True upon completion.
        """

        module_name = self.get_module_name(top_p)
        cpp_name = path.join(self.tempdir, f"{top_p.name}.cpp")

        cpp_tmpl = '#include "' + top_p.name + '.h"\n\n'

        if body_type is PyInteractiveBody:
            cpp_tmpl += f"{module_name}* {module_name}::singleton = nullptr;\n"

        cpp_tmpl += f"{module_name}::{module_name}(sc_module_name name): " + \
            "sc_module(name) {\n"

        cpp_tmpl_ind = ""

        if body_type is PyInteractiveBody:
            cpp_tmpl_ind = "if (singleton == nullptr) {\n"
            cpp_tmpl_ind += "singleton = this;\n"
            cpp_tmpl_ind += "} else {\n"
            cpp_tmpl_ind += f"std::cerr << \"attempted to construct multiple python for {module_name} modules - not supported!\" << std::endl;\n"
            cpp_tmpl_ind += "exit(-1);\n"
            cpp_tmpl_ind += "}\n"

        if body_type is PyConstBody:
            cpp_tmpl_ind = 'no_ins = 0;\n'
        else:
            cpp_tmpl_ind += f'no_ins = {len(top_p.inPorts)};\n'
        cpp_tmpl_ind += f'no_outs = {len(top_p.outPorts)};\n'

        if body_type is PyInteractiveBody:
            cpp_tmpl_ind += f'const char* sc_module_name = "{module_name.lower()}_sysc";\n'
            cpp_tmpl_ind += 'PyImport_AddModule(sc_module_name);\n'
            cpp_tmpl_ind += 'PyObject* sys_modules = PyImport_GetModuleDict();\n'
            cpp_tmpl_ind += 'PyObject* module = PyInit_sysc();\n'
            cpp_tmpl_ind += 'PyDict_SetItemString(sys_modules, sc_module_name, module);\n'

        if body_type is not PyConstBody:
            cpp_tmpl_ind += f'this->pName = PyUnicode_DecodeFSDefault("{top_p.name}");\n'
            cpp_tmpl_ind += "this->pModule = PyImport_Import(this->pName);\n"
            cpp_tmpl_ind += "if (this->pModule == NULL) {\n"
            cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
            cpp_tmpl_ind += f'std::cout << "failed to import {top_p.name} python module." << std::endl;\n'
            cpp_tmpl_ind += "exit(-1);\n"
            cpp_tmpl_ind += "}\n"
            cpp_tmpl_ind += "this->pBody = PyObject_GetAttrString(this->pModule, \"body\");\n"
            cpp_tmpl_ind += "if (this->pBody == NULL) {\n"
            cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
            cpp_tmpl_ind += f'std::cout << "failed to import {top_p.name} python body." << std::endl;\n'
            cpp_tmpl_ind += "exit(-1);\n"
            cpp_tmpl_ind += "}\n"

            if body_type is PyInteractiveBody:
                cpp_tmpl_ind += "this->pNode = PyObject_GetAttrString(this->pModule, \"node\");\n"
                cpp_tmpl_ind += "if (this->pBody == NULL) {\n"
                cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
                cpp_tmpl_ind += f'std::cout << "failed to import {top_p.name} python interactive node." << std::endl;\n'
                cpp_tmpl_ind += "exit(-1);\n"
                cpp_tmpl_ind += "}\n"

            cpp_tmpl_ind += "PyObject *runtimeModule = PyImport_Import(PyUnicode_DecodeFSDefault(\"deltalanguage.runtime\"));\n"
            cpp_tmpl_ind += "if (runtimeModule == NULL) {\n"
            cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
            cpp_tmpl_ind += f'std::cout << "failed to import deltalanguage runtime in {top_p.name}." << std::endl;\n'
            cpp_tmpl_ind += "exit(-1);\n"
            cpp_tmpl_ind += "}\n"
            cpp_tmpl_ind += "this->pExit = PyObject_GetAttrString(runtimeModule, \"DeltaRuntimeExit\");\n"
            cpp_tmpl_ind += "if (this->pExit == NULL) {\n"
            cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
            cpp_tmpl_ind += f'std::cout << "failed to import exit exception object from deltalanguage runtime in {top_p.name}." << std::endl;\n'
            cpp_tmpl_ind += "exit(-1);\n"
            cpp_tmpl_ind += "}\n"

            for port in top_p.inPorts:
                cpp_tmpl_ind += f"this->type_{self.get_sysc_port_name(port)} = PyObject_GetAttrString(this->pModule, \"{self.get_sysc_port_name(port)}\");\n"
                cpp_tmpl_ind += f"if (this->type_{self.get_sysc_port_name(port)} == NULL){{\n"
                cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"
                cpp_tmpl_ind += f"std::cout << \"failed to import type for in port {port.name} in {top_p.name}.\" << std::endl;\n"
                cpp_tmpl_ind += "exit(-1);\n"
                cpp_tmpl_ind += "}\n"
                cpp_tmpl_ind += f"{self.get_sysc_port_name(port)} = NULL;\n"

        for port in top_p.outPorts:
            if body_type is not PyConstBody:
                cpp_tmpl_ind += f"this->type_{self.get_sysc_port_name(port)} = PyObject_GetAttrString(this->pModule, \"{self.get_sysc_port_name(port)}\");\n"
                cpp_tmpl_ind += f"if (this->type_{self.get_sysc_port_name(port)} == NULL){{\n"
                cpp_tmpl_ind += "if (PyErr_Occurred()) PyErr_Print();\n"

                if port.name:
                    cpp_tmpl_ind += f"std::cout << \"failed to import type for out port {port.name} in {top_p.name}.\" << std::endl;\n"
                else:
                    cpp_tmpl_ind += f"std::cout << \"failed to import return type in {top_p.name}.\" << std::endl;\n"
                cpp_tmpl_ind += "exit(-1);\n"
                cpp_tmpl_ind += "}\n"
            cpp_tmpl_ind += f"{self.get_sysc_port_name(port)} = NULL;\n"

        if body_type is not PyConstBody:
            cpp_tmpl_ind += "Py_XDECREF(this->pName);\n"
            cpp_tmpl_ind += "Py_XDECREF(this->pModule);\n"

        cpp_tmpl_ind += "SC_THREAD(body);\n"
        cpp_tmpl += textwrap.indent(cpp_tmpl_ind, indent_prefix) + "}\n\n"

        if body_type not in [PyConstBody, PyInteractiveBody]:
            for port in top_p.inPorts:
                port_type = self.load_port_type(port)
                cpp_tmpl += f"PyObject* {module_name}::get_{self.get_sysc_port_name(port)}(){{\n"
                cpp_tmpl += textwrap.indent(f"if ({self.get_sysc_port_name(port)} == NULL) return Py_None;\n", indent_prefix)
                if port.optional:
                    cpp_tmpl += textwrap.indent(f"if (!{self.get_sysc_port_name(port)}->nb_read(bits_{self.get_sysc_port_name(port)})) return Py_None;\n", indent_prefix)
                else:
                    cpp_tmpl += textwrap.indent(f"bits_{self.get_sysc_port_name(port)} = {self.get_sysc_port_name(port)}->read();\n", indent_prefix)
                cpp_tmpl += textwrap.indent(
                    f"return PyObject_CallMethodObjArgs(this->type_{self.get_sysc_port_name(port)}, PyUnicode_FromString(\"unpack\"), PyBytes_FromStringAndSize(bits_{self.get_sysc_port_name(port)}.to_string().c_str(), {port_type.size}), NULL);\n", 
                    indent_prefix
                )
                cpp_tmpl += "};\n"

        if body_type is PyInteractiveBody:
            cpp_tmpl += f"PyMethodDef {module_name}::SysCMethods[] = {{\n"
            cpp_tmpl += "{\"receive\", sc_receive, METH_VARARGS, \"Receives data from the systemC interface\"},\n"
            cpp_tmpl += "{\"send\", sc_send, METH_VARARGS, \"Sends data to the systemC interface\"},\n"
            cpp_tmpl += "{NULL, NULL, 0, NULL}\n"
            cpp_tmpl += "};\n"

            cpp_tmpl += f"PyModuleDef {module_name}::SysCModule = {{\n"
            cpp_tmpl += f"PyModuleDef_HEAD_INIT, \"{module_name.lower()}_sysc\", NULL, -1, SysCMethods,\n"
            cpp_tmpl += "NULL, NULL, NULL, NULL\n"
            cpp_tmpl += "};\n"

            cpp_tmpl += f"PyObject* {module_name}::PyInit_sysc(void)\n"
            cpp_tmpl += "{\n"
            cpp_tmpl += f"std::cout << \"{module_name}::PyInit_sysc() called \" << std::endl;\n"
            cpp_tmpl += "return PyModule_Create(&SysCModule);\n"
            cpp_tmpl += "}\n"

            cpp_tmpl += f"PyObject* {module_name}::sc_receive(PyObject *self, PyObject *args){{\n"
            cpp_tmpl += textwrap.indent('const char * inport; \n', indent_prefix)
            cpp_tmpl += textwrap.indent('bool retval; \n', indent_prefix)

            for port in top_p.inPorts:
                cpp_tmpl += f"{self.as_c_type(port.type)} bv_{self.get_sysc_port_name(port)};\n"

            cpp_tmpl += textwrap.indent(
                'if (!PyArg_ParseTuple(args, "s", &inport )) {\n', 
                indent_prefix
            )
            cpp_tmpl += textwrap.indent(
                'std::cout << "sc_receive::ERROR" << std::endl;\n',
                indent_prefix * 2
            )
            cpp_tmpl += textwrap.indent('return NULL;\n', indent_prefix * 2)
            cpp_tmpl += textwrap.indent('}\n', indent_prefix)
            cpp_tmpl += textwrap.indent('std::string ins (inport);\n', indent_prefix)

            num_ports = len(top_p.inPorts)
            for port in top_p.inPorts:
                port_type = self.load_port_type(port)
                if num_ports > 1:
                    cpp_tmpl += textwrap.indent(
                        f"if (ins == \"{port.name}\") {{\n", indent_prefix
                    )
                if port.optional:
                    cpp_tmpl += textwrap.indent(f"if (singleton->{self.get_sysc_port_name(port)} == NULL) return Py_None;\n", indent_prefix * 2)
                    cpp_tmpl += textwrap.indent(
                        f"retval = singleton->{self.get_sysc_port_name(port)}->nb_read(bv_{self.get_sysc_port_name(port)});\n",
                        indent_prefix * 2
                    )
                    cpp_tmpl += textwrap.indent("if (retval == false){\n", indent_prefix * 2)
                    cpp_tmpl += textwrap.indent("return Py_None;\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent("}\n", indent_prefix * 2)
                else:
                    cpp_tmpl += textwrap.indent(
                        f"singleton->{self.get_sysc_port_name(port)}->read(bv_{self.get_sysc_port_name(port)});\n",
                        indent_prefix * 2
                    )
                cpp_tmpl += f"return PyObject_CallMethodObjArgs(singleton->type_{self.get_sysc_port_name(port)}, " + \
                    f"PyUnicode_FromString(\"unpack\"), PyBytes_FromStringAndSize(bv_{self.get_sysc_port_name(port)}.to_string().c_str(), " + \
                    f"{port_type.size}), NULL);\n"
                if num_ports > 1:
                    cpp_tmpl += "}\n"

            cpp_tmpl += textwrap.indent('PyErr_SetString(PyExc_TypeError, "Unrecognized argument");\n', indent_prefix)
            cpp_tmpl += textwrap.indent('return (PyObject *) NULL;\n', indent_prefix)
            cpp_tmpl += "}\n"

            cpp_tmpl += f"PyObject* {module_name}::sc_send(PyObject *self, PyObject *args){{\n"
            cpp_tmpl += textwrap.indent('const char * outport;\n', indent_prefix)
            cpp_tmpl += textwrap.indent('const char * data;\n', indent_prefix)
            cpp_tmpl += textwrap.indent('if (!PyArg_ParseTuple(args, "ss*", &outport, &data)) {\n', indent_prefix)
            cpp_tmpl += textwrap.indent('std::cout << "sc_send::ERROR" << std::endl;\n', indent_prefix * 2)
            cpp_tmpl += textwrap.indent('return NULL;\n', indent_prefix * 2)
            cpp_tmpl += textwrap.indent('}\n', indent_prefix)
            cpp_tmpl += textwrap.indent('singleton->wait(1, SC_NS);\n', indent_prefix)
            cpp_tmpl += textwrap.indent('std::string outs (outport);\n', indent_prefix)

            num_ports = len(top_p.outPorts)
            for port in top_p.outPorts:
                if num_ports > 1:
                    cpp_tmpl += textwrap.indent(f"if ((outs == \"{port.name}\") && (singleton->{self.get_sysc_port_name(port)} != NULL)){{\n", indent_prefix)
                    cpp_tmpl += textwrap.indent(f"singleton->{self.get_sysc_port_name(port)}->write(data);\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent("}\n", indent_prefix)
                else:
                    cpp_tmpl += textwrap.indent(f"if (singleton->{self.get_sysc_port_name(port)} != NULL) singleton->{self.get_sysc_port_name(port)}->write(data);\n", indent_prefix)
            cpp_tmpl += textwrap.indent('return Py_None;\n', indent_prefix)
            cpp_tmpl += "}\n"

        if body_type is not PyInteractiveBody:
            if body_type is PyConstBody:
                body = dill.loads(self._bodies[body_id].python.dillImpl)
                try:
                    val = body.eval()
                except DeltaRuntimeExit:
                    raise ValueError(
                        "DeltaRuntimeExit raised during build process."
                    )
                except:
                    raise ValueError(
                        "Exception raised during build process."
                    )
            for i, port in enumerate(top_p.outPorts):
                port_type = self.load_port_type(port)
                cpp_tmpl += f"\nvoid {module_name}::set_{self.get_sysc_port_name(port)}(){{\n"
                cpp_tmpl += textwrap.indent(f"if ({self.get_sysc_port_name(port)} != NULL){{\n", indent_prefix)

                if body_type is PyConstBody:
                    if len(top_p.outPorts) > 1:
                        port_val = val[i]
                    else:
                        port_val = val
                    if port_val is not None:
                        cpp_tmpl += textwrap.indent(
                            f'{self.get_sysc_port_name(port)}->nb_write("{port_type.pack(port_val).decode("ascii")}");\n',
                            indent_prefix * 2
                        )
                    else:
                        raise ValueError(f'None returned by constant node {top_p.name}.')
                else:
                    if len(top_p.outPorts) > 1:
                        cpp_tmpl += textwrap.indent(
                            f"PyObject* acc_i = Py_BuildValue(\"i\", {i});\n",
                            indent_prefix * 2
                        )
                        cpp_tmpl += textwrap.indent(
                            f"PyObject* pyRet = PyObject_GetItem(this->pyC, acc_i);\n",
                            indent_prefix * 2
                        )
                    else:
                        cpp_tmpl += textwrap.indent(f"PyObject* pyRet = this->pyC;\n", indent_prefix * 2)

                    cpp_tmpl += textwrap.indent("if (pyRet != Py_None){\n", indent_prefix * 2)
                    cpp_tmpl += textwrap.indent(
                        f"PyObject* pyBits = PyObject_CallMethodObjArgs(this->type_{self.get_sysc_port_name(port)}, PyUnicode_FromString(\"pack\"), pyRet, NULL);\n",
                        indent_prefix * 3
                    )
                    cpp_tmpl += textwrap.indent("PyObject* pyErr = PyErr_Occurred();\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent("if (pyErr != NULL) {\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent("PyErr_Print();\n", indent_prefix * 4)
                    cpp_tmpl += textwrap.indent("PyErr_Clear();\n", indent_prefix * 4)
                    cpp_tmpl += textwrap.indent("exit(-1);\n", indent_prefix * 4)
                    cpp_tmpl += textwrap.indent("}\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent(f"char* bitsRet = PyBytes_AsString(pyBits);\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent(f"{self.get_sysc_port_name(port)}->write(bitsRet);\n", indent_prefix * 3)
                    cpp_tmpl += textwrap.indent("}\n", indent_prefix * 2)
                cpp_tmpl += textwrap.indent("}\n", indent_prefix)
                cpp_tmpl += "};\n"

        cpp_tmpl += f'\nvoid {module_name}::body(){{\n'

        if body_type is not PyInteractiveBody:
            cpp_tmpl += textwrap.indent('while (true) {\n', indent_prefix)

        cpp_tmpl_ind = ""

        if body_type is not PyConstBody:
            if body_type is PyInteractiveBody:
                cpp_tmpl_ind += 'this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"), this->pNode , NULL);\n'
            else:
                if top_p.inPorts:
                    args = [f'get_{self.get_sysc_port_name(port)}()' for port in top_p.inPorts]
                    cpp_tmpl_ind += 'this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"),' + ",".join(args) +' ,NULL);\n'
                else:
                    cpp_tmpl_ind += 'this->pyC = PyObject_CallMethod(this->pBody, "eval", NULL);\n'
            cpp_tmpl_ind += "PyObject* pyErr = PyErr_Occurred();\n"
            cpp_tmpl_ind += "if (pyErr != NULL) {\n"
            cpp_tmpl_ind += textwrap.indent("if (PyErr_ExceptionMatches(this->pExit)) {\n", indent_prefix)
            cpp_tmpl_ind += textwrap.indent("PyErr_Clear();\n", indent_prefix * 2)
            cpp_tmpl_ind += textwrap.indent("sc_stop();\n", indent_prefix * 2)

            if body_type is not PyInteractiveBody:
                cpp_tmpl_ind += textwrap.indent("break;\n", indent_prefix * 2)
            cpp_tmpl_ind += textwrap.indent("} else {\n", indent_prefix)
            cpp_tmpl_ind += textwrap.indent("PyErr_Print();\n", indent_prefix * 2)
            cpp_tmpl_ind += textwrap.indent("PyErr_Clear();\n", indent_prefix * 2)
            cpp_tmpl_ind += textwrap.indent("exit(-1);\n", indent_prefix * 2)
            cpp_tmpl_ind += textwrap.indent("}\n", indent_prefix)
            cpp_tmpl_ind += "}\n"

        if body_type is not PyInteractiveBody:
            if body_type is PyConstBody:
                for port in top_p.outPorts:
                    cpp_tmpl_ind += f'set_{self.get_sysc_port_name(port)}();\n'
            else:
                cpp_tmpl_ind += "if (this->pyC != Py_None) {\n"
                for port in top_p.outPorts:
                    cpp_tmpl_ind += textwrap.indent(
                        f'set_{self.get_sysc_port_name(port)}();\n',
                        indent_prefix
                    )
                cpp_tmpl_ind += "}\n"

        if body_type is not PyInteractiveBody:
            cpp_tmpl_ind += 'wait(1, SC_NS);\n'

        cpp_tmpl += textwrap.indent(cpp_tmpl_ind, indent_prefix * 2)

        if body_type is not PyInteractiveBody:
            cpp_tmpl += textwrap.indent('}\n', indent_prefix)

        cpp_tmpl += '};\n'

        cpp_tmpl += f"\nint {module_name}::get_no_inputs() const\n"
        cpp_tmpl += '{\n'
        cpp_tmpl += textwrap.indent('return no_ins;\n', indent_prefix)
        cpp_tmpl += '};\n'

        cpp_tmpl += f"\nint {module_name}::get_no_outputs() const\n"
        cpp_tmpl += '{\n'
        cpp_tmpl += textwrap.indent('return no_outs;\n', indent_prefix)
        cpp_tmpl += '};\n'

        with open(cpp_name, "w") as out_file:
            out_file.write(cpp_tmpl)

        return True

    def _get_cpp(self, top_p, after):
        """Get the C++ code containing the node's SystemC module after
        it has been built.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.
        after : Coroutine
            Process which builds the C++ code.

        Returns
        -------
        BuildArtifact
            The C++ code implementing the node's SystemC module.
        """
        return BuildArtifact(f"{top_p.name}.cpp", self, after=after)

    async def _build_objects(self, top_p, after):
        """Build the object file using gcc.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node. Used to get the node's name.
        after : list
            :class:`Coroutine` objects that need to finish before the
            binary object can be built. This should include the processes
            for building the node's header and C++ files.

        Returns
        -------
        Bool
            Returns True once build is complete.
        """
        done = await self._run_gcc(top_p.name, after)
        return done

    def _get_binary(self, top_p, after):
        """Get the binary object for the node.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node. Used to get the node's name.
        after : Coroutine
            Build process that needs to complete before the binary object
            is ready.

        Returns
        -------
        BuildArtifact
            The built binary object for the node.
        """
        return self._get_o(top_p.name, after)

    def pythonate(self, top_p, body_id):
        """Generates all the build outputs for this node.

        Parameters
        ----------
        top_p
            ``capnp`` object describing the node.

        Returns
        -------
        dict
            A map of strings to
            :py:class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>`
            objects containing different parts of the node's SystemC
            implementation:

            - "cpp": the C++ file
            - "h": the header file
            - "py": the Python file (only exists if the node is not constant)
            - "o": the built binary object
        """
        body_class = self._bodies[body_id].which()
        if "python" in body_class:
            body = self._bodies[body_id].python.dillImpl
        if "interactive" in body_class:
            body = self._bodies[body_id].interactive.dillImpl

        body_types = {b"PyConstBody": PyConstBody,
                      b"PyInteractiveBody": PyInteractiveBody}
        match = re.search(b"Py(Const|Interactive)Body", body)
        if match:
            body_type = body_types[match.group(0)]
        else:
            body_type = None

        make_cpp = self._make_cpp(top_p, body_type, body_id)
        cpp = self._get_cpp(top_p, after=make_cpp)
        make_h = self._make_h(top_p, body_type)
        h = self._get_h(top_p, after=make_h)
        if body_type is not PyConstBody:
            make_py = self._make_py(top_p, body, body_type)
            py = self._get_py(top_p, after=make_py)
        build_objects = self._build_objects(top_p, after=[make_cpp, make_h])
        binary = self._get_binary(top_p, after=build_objects)

        # return a set of build artifacts
        built_artifacts = dict()
        built_artifacts["cpp"] = cpp
        built_artifacts["h"] = h
        if body_type is not PyConstBody:
            built_artifacts["py"] = py
        built_artifacts["o"] = binary

        return built_artifacts
