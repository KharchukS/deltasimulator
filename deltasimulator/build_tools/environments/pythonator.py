import asyncio
from os import path
import sysconfig
from io import StringIO
import textwrap

import dill

from deltalanguage.wiring import PyConstBody, PyInteractiveBody

from .cppenv import CPPEnv
from deltasimulator.build_tools import BuildArtifact, cogify
from deltasimulator.build_tools.utils import multiple_waits

class PythonatorEnv(CPPEnv):
    """Environment for generating SystemC modules of Python nodes.

    :meth:`cogify` is used to automatically generate the Python, C++ and
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
            capnp object describing the port.

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
            return "sysc_return"

    @staticmethod
    def get_module_name(top_p):
        """Get the name of the node's SystemC module.

        Parameters
        ----------
        top_p
            capnp object describing the node.

        Returns
        -------
        str
            The name of the node's module.
            The format used is `{Node_Name}_module`, where
            `Node_Name` is the capitalised version of the name of the node.
        """
        return "_".join([word.capitalize() for word in top_p.name.split("_")])\
            + "_module"


    async def _make_py(self, top_p, df_body):
        """Makes Python script for the node.

        The Python script contains the node's body as well as data types
        for input and output ports.

        Parameters
        ----------
        top_p
            capnp object describing the node.

        Returns
        -------
        bool
            Returns True on completion.
        """
        body_type = type(dill.loads(df_body))

        # df_ prefix to variables used to avoid namespace clashes with cog
        py_tmpl = """
        import dill
        /*[[[cog
            if body_type is PyInteractiveBody:
                cog.outl(f"import {module_name.lower()}_sysc")
            cog.outl(f"body = dill.loads({df_body})")
            for port in top_p.inPorts:
                cog.outl(f"{self.get_sysc_port_name(port)} = dill.loads({port.type})")
            for port in top_p.outPorts:
                cog.outl(f"{self.get_sysc_port_name(port)} = dill.loads({port.type})")
            if body_type is PyInteractiveBody:
                cog.outl("class SysBridgeNode:")
                cog.outl("    def __init__(self): ")
                inports_list = []
                for port in top_p.inPorts:
                    inports_list.append(port.name)
                inports_str = '[' + '"{0}"'.format('", "'.join(inports_list)) + ']'
                if (len(inports_list) > 0):
                    cog.outl(f"        self.in_queues = dict.fromkeys({inports_str}) ")
                cog.outl("    def send(self,val):")
                if len(top_p.outPorts) > 1:
                    for port in top_p.outPorts:
                        cog.outl(f"        if val.{port.name} is not None:")
                        cog.outl(f"            {module_name.lower()}_sysc.send(\\"{port.name}\\", {self.get_sysc_port_name(port)}.pack(val.{port.name}))")
                else:
                    cog.outl(f"        if val is not None:")
                    cog.outl(f"            {module_name.lower()}_sysc.send(\\"{port.name}\\", {self.get_sysc_port_name(port)}.pack(val))")
                cog.outl("    def receive(self, *args: str):")
                if (len(inports_list) == 0):
                    cog.outl("        raise RuntimeError ")
                cog.outl("        if args: ")
                cog.outl("            in_queue = {name: in_q for name, in_q in self.in_queues.items() if name in args}")
                cog.outl("        else: ")
                cog.outl("            in_queue = self.in_queues ")
                cog.outl("        values = {} ")
                cog.outl("        if in_queue: ")
                cog.outl("             for req in in_queue: ")
                cog.outl(f"                 values[req] = {module_name.lower()}_sysc.receive(req)")
                cog.outl("        if len(values) == 1 and args: ")
                cog.outl("            return values[list(values)[0]] ")
                cog.outl("        else: ")
                cog.outl("            return values")
                cog.outl("node = SysBridgeNode()")
        ]]]*/
        //[[[end]]]
        """
        body_index = top_p.body
        body_file = path.join(self.tempdir, f"{top_p.name}.py")
        module_name = self.get_module_name(top_p)

        with open(body_file, "wb") as py_file:
            py_file.write(cogify(py_tmpl, globals=dict(globals(), **locals())))
        return True

    def _get_py(self, top_p, after):
        """Get the node's Python script.

        Parameters
        ----------
        top_p
            capnp object describing the node.
        after : Coroutine
            Process that needs to complete before the Python script is ready.

        Returns
        -------
        BuildArtifact
            The Python script for this node.
        """
        return BuildArtifact(f"{top_p.name}.py", self, after=after)

    async def _make_h(self, top_p,
                      body_type # pylint: disable=unused-argument
                      ):
        """Generate the Header file for this node.

        Parameters
        ----------
        top_p
            capnp object describing the node.
        body_type
            The type of body this node has. Used to check if the node is a
            constant node or not.

        Returns
        -------
        bool
            Returns True upon completion.
        """

        h_tmpl = """\
        #include <string>
        #include <systemc>
        using namespace sc_core;
        /*[[[cog
            if body_type is not PyConstBody:
                cog.outl('#include "Python.h"')
        ]]]*/
        //[[[end]]]

        //[[[cog cog.outl(f"#ifndef __{top_p.name.upper()}_MODULE__"); cog.outl(f"#define __{top_p.name.upper()}_MODULE__") ]]]
        //[[[end]]]

        //[[[cog cog.outl(f"class {module_name} : public sc_module") ]]]
        //[[[end]]]
        {
        private:
            /*[[[cog
                if body_type is not PyConstBody:
                    cog.outl("PyObject *pBody, *pName, *pModule, *pyC, *pExit;")
                if body_type is PyInteractiveBody:
                    cog.outl("PyObject *runtimeModule, *pNode;")
                    cog.outl("static PyObject* sc_receive(PyObject *self, PyObject *args);")
                    cog.outl("static PyObject* sc_send(PyObject *self, PyObject *args);")
                    cog.outl("static PyObject* PyInit_sysc(void);")
                    cog.outl("static PyMethodDef SysCMethods[];")
                    cog.outl("static PyModuleDef SysCModule;")
                    cog.outl(f"static {module_name}* singleton;")
                    cog.outl("void init();")
                    cog.outl("void store();")
                    cog.outl("void run();")
            ]]]*/
            //[[[end]]]
            uint64_t no_ins, no_outs;
            /*[[[cog
                if body_type is not PyConstBody:
                    for port in top_p.inPorts:
                        cog.outl(f"PyObject* type_{self.get_sysc_port_name(port)};")
                        cog.outl(f"PyObject* get_{self.get_sysc_port_name(port)}();")
                        cog.outl(f"{self.as_c_type(port.type)} bits_{self.get_sysc_port_name(port)};")
                for port in top_p.outPorts:
                    if body_type is not PyConstBody:
                        cog.outl(f"PyObject* type_{self.get_sysc_port_name(port)};")
                        cog.outl(f"{self.as_c_type(port.type)} bits_{self.get_sysc_port_name(port)};")
                    cog.outl(f"void set_{self.get_sysc_port_name(port)}();")
            ]]]*/
            //[[[end]]]
        public:
            uint64_t no_inputs, no_outputs;
            /*[[[cog
                    if body_type is not PyConstBody:
                        for port in top_p.inPorts:
                            cog.outl(f"sc_fifo<{self.as_c_type(port.type)}>* {self.get_sysc_port_name(port)};")
                    for port in top_p.outPorts:
                        cog.outl(f"sc_fifo<{self.as_c_type(port.type)}>* {self.get_sysc_port_name(port)};")
            ]]]*/
            //[[[end]]]
            int get_no_inputs() const;
            int get_no_outputs() const;
            void body();
            //[[[cog cog.outl(f"SC_HAS_PROCESS({module_name});"); cog.outl(f"{module_name}(sc_module_name name);") ]]]
            //[[[end]]]
        };
        #endif
        """

        module_name = self.get_module_name(top_p)
        h_name = path.join(self.tempdir, f"{top_p.name}.h")

        with open(h_name, "wb") as out_file:
            out_file.write(cogify(h_tmpl, globals=dict(globals(), **locals())))
        return True

    def _get_h(self, top_p, after):
        """Get the Header file for the node.

        Parameters
        ----------
        top_p
            capnp object describing the node.
        after : Coroutine
            The process that constructs the Header file.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        return BuildArtifact(f"{top_p.name}.h", self, after=after)

    async def _make_cpp(self, top_p,
                        body_type # pylint: disable=unused-argument
                        ):
        """Construct the node's SystemC module.

        Parameters
        ----------
        top_p
            capnp object describing the node.
        body_type
            The type of body this node has. Used to check if the node is a
            constant node or not.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        cpp_tmpl = """\
        //[[[cog cog.outl('#include "' + top_p.name + '.h"') ]]]
        //[[[end]]]

        /*[[[cog
        if body_type is PyInteractiveBody:
            cog.outl(f"{module_name}* {module_name}::singleton = nullptr;")
        ]]]*/
        //[[[end]]]
        //[[[cog cog.outl(f"{module_name}::{module_name}(sc_module_name name): sc_module(name) {{") ]]]
        //[[[end]]]
            /*[[[cog
            if body_type is PyInteractiveBody:
                cog.outl("if (singleton == nullptr) {")
                cog.outl("singleton = this;")
                cog.outl("} else {")
                cog.outl(f"std::cerr << \\"attempted to construct multiple python for {module_name} modules - not supported!\\" << std::endl;")
                cog.outl("exit(-1);")
                cog.outl("}")
            if body_type is PyConstBody:
                cog.outl('no_ins = 0;')
            else:
                cog.outl(f'no_ins = {len(top_p.inPorts)};')
            cog.outl(f'no_outs = {len(top_p.outPorts)};')
            if body_type is PyInteractiveBody:
                cog.outl(f'const char* sc_module_name = "{module_name.lower()}_sysc";')
                cog.outl('PyImport_AddModule(sc_module_name);')
                cog.outl('PyObject* sys_modules = PyImport_GetModuleDict();')
                cog.outl('PyObject* module = PyInit_sysc();')
                cog.outl('PyDict_SetItemString(sys_modules, sc_module_name, module);')
            if body_type is not PyConstBody:
                cog.outl(f'this->pName = PyUnicode_DecodeFSDefault("{top_p.name}");')
                cog.outl("this->pModule = PyImport_Import(this->pName);")
                cog.outl("if (this->pModule == NULL) {")
                cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                cog.outl(f'std::cout << "failed to import {top_p.name} python module." << std::endl;')
                cog.outl("exit(-1);")
                cog.outl("}")
                cog.outl("this->pBody = PyObject_GetAttrString(this->pModule, \\"body\\");")
                cog.outl("if (this->pBody == NULL) {")
                cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                cog.outl(f'std::cout << "failed to import {top_p.name} python body." << std::endl;')
                cog.outl("exit(-1);")
                cog.outl("}")
                if body_type is PyInteractiveBody:
                    cog.outl("this->pNode = PyObject_GetAttrString(this->pModule, \\"node\\");")
                    cog.outl("if (this->pBody == NULL) {")
                    cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                    cog.outl(f'std::cout << "failed to import {top_p.name} python interactive node." << std::endl;')
                    cog.outl("exit(-1);")
                    cog.outl("}")
                cog.outl("PyObject *runtimeModule = PyImport_Import(PyUnicode_DecodeFSDefault(\\"deltalanguage.runtime\\"));")
                cog.outl("if (runtimeModule == NULL) {")
                cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                cog.outl(f'std::cout << "failed to import deltalanguage runtime in {top_p.name}." << std::endl;')
                cog.outl("exit(-1);")
                cog.outl("}")
                cog.outl("this->pExit = PyObject_GetAttrString(runtimeModule, \\"DeltaRuntimeExit\\");")
                cog.outl("if (this->pExit == NULL) {")
                cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                cog.outl(f'std::cout << "failed to import exit exception object from deltalanguage runtime in {top_p.name}." << std::endl;')
                cog.outl("exit(-1);")
                cog.outl("}")
                for port in top_p.inPorts:
                    cog.outl(f"this->type_{self.get_sysc_port_name(port)} = PyObject_GetAttrString(this->pModule, \\"{self.get_sysc_port_name(port)}\\");")
                    cog.outl(f"if (this->type_{self.get_sysc_port_name(port)} == NULL){{")
                    cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                    cog.outl(f"std::cout << \\"failed to import type for in port {port.name} in {top_p.name}.\\" << std::endl;")
                    cog.outl("exit(-1);")
                    cog.outl("}")
                    cog.outl(f"{self.get_sysc_port_name(port)} = NULL;")
                for port in top_p.outPorts:
                    if body_type is not PyConstBody:
                        cog.outl(f"this->type_{self.get_sysc_port_name(port)} = PyObject_GetAttrString(this->pModule, \\"{self.get_sysc_port_name(port)}\\");")
                        cog.outl(f"if (this->type_{self.get_sysc_port_name(port)} == NULL){{")
                        cog.outl("if (PyErr_Occurred()) PyErr_Print();")
                        if port.name:
                            cog.outl(f"std::cout << \\"failed to import type for out port {port.name} in {top_p.name}.\\" << std::endl;")
                        else:
                            cog.outl(f"std::cout << \\"failed to import return type in {top_p.name}.\\" << std::endl;")
                        cog.outl("exit(-1);")
                        cog.outl("}")
                    cog.outl(f"{self.get_sysc_port_name(port)} = NULL;")
            if body_type is not PyConstBody:
                cog.outl("Py_XDECREF(this->pName);")
                cog.outl("Py_XDECREF(this->pModule);")
            ]]]*/
            //[[[end]]]
            SC_THREAD(body);
        }

        /*[[[cog
            if body_type not in [PyConstBody, PyInteractiveBody]:
                for port in top_p.inPorts:
                    port_type = self.load_port_type(port)
                    cog.outl(f"PyObject* {module_name}::get_{self.get_sysc_port_name(port)}(){{")
                    cog.outl(f"    if ({self.get_sysc_port_name(port)} == NULL) return Py_None;")
                    if port.optional:
                        cog.outl(f"    if (!{self.get_sysc_port_name(port)}->nb_read(bits_{self.get_sysc_port_name(port)})) return Py_None;")
                    else:
                        cog.outl(f"    bits_{self.get_sysc_port_name(port)} = {self.get_sysc_port_name(port)}->read();")
                    cog.outl(f"    return PyObject_CallMethodObjArgs(this->type_{self.get_sysc_port_name(port)}, PyUnicode_FromString(\\"unpack\\"), PyBytes_FromStringAndSize(bits_{self.get_sysc_port_name(port)}.to_string().c_str(), {port_type.size}), NULL);")
                    cog.outl("};")
            if body_type is PyInteractiveBody:
                cog.outl(f"PyMethodDef {module_name}::SysCMethods[] = {{")
                cog.outl("{\\"receive\\", sc_receive, METH_VARARGS, \\"Receives data from the systemC interface\\"},")
                cog.outl("{\\"send\\", sc_send, METH_VARARGS, \\"Sends data to the systemC interface\\"},")
                cog.outl("{NULL, NULL, 0, NULL}")
                cog.outl("};")

                cog.outl(f"PyModuleDef {module_name}::SysCModule = {{")
                cog.outl(f"PyModuleDef_HEAD_INIT, \\"{module_name.lower()}_sysc\\", NULL, -1, SysCMethods,")
                cog.outl("NULL, NULL, NULL, NULL")
                cog.outl("};")

                cog.outl(f"PyObject* {module_name}::PyInit_sysc(void)")
                cog.outl("{")
                cog.outl(f"std::cout << \\"{module_name}::PyInit_sysc() called \\" << std::endl;")
                cog.outl("return PyModule_Create(&SysCModule);")
                cog.outl("}")

                cog.outl(f"PyObject* {module_name}::sc_receive(PyObject *self, PyObject *args){{")
                cog.outl('    const char * inport; ')
                cog.outl('    bool retval; ')
                for port in top_p.inPorts:
                    cog.outl(f"{self.as_c_type(port.type)} bv_{self.get_sysc_port_name(port)};")
                cog.outl('    if (!PyArg_ParseTuple(args, "s", &inport )) {')
                cog.outl('        std::cout << "sc_receive::ERROR" << std::endl;')
                cog.outl('        return NULL;')
                cog.outl('    }')
                cog.outl('    std::string ins (inport);')
                num_ports = len(top_p.inPorts)
                for port in top_p.inPorts:
                    port_type = self.load_port_type(port)
                    if num_ports > 1:
                        cog.outl(f"    if (ins == \\"{port.name}\\") {{")
                    if port.optional:
                        cog.outl(f"      retval = singleton->{self.get_sysc_port_name(port)}->nb_read(bv_{self.get_sysc_port_name(port)});")
                        cog.outl("      if (retval == false){")
                        cog.outl("          return Py_None;")
                        cog.outl("      }")
                    else :
                        cog.outl(f"      singleton->{self.get_sysc_port_name(port)}->read(bv_{self.get_sysc_port_name(port)});")
                    cog.outl(f"return PyObject_CallMethodObjArgs(singleton->type_{self.get_sysc_port_name(port)}, PyUnicode_FromString(\\"unpack\\"), PyBytes_FromStringAndSize(bv_{self.get_sysc_port_name(port)}.to_string().c_str(), {port_type.size}), NULL);")
                    if num_ports > 1:
                        cog.outl("}")
                cog.outl('    PyErr_SetString(PyExc_TypeError, "Unrecognized argument");')
                cog.outl('    return (PyObject *) NULL;')
                cog.outl("}")

                cog.outl(f"PyObject* {module_name}::sc_send(PyObject *self, PyObject *args){{")
                cog.outl('    const char * outport;')
                cog.outl('    const char * data;')
                cog.outl('    if (!PyArg_ParseTuple(args, "ss*", &outport, &data)) {')
                cog.outl('        std::cout << "sc_send::ERROR" << std::endl;')
                cog.outl('        return NULL;')
                cog.outl('    }')
                cog.outl('    singleton->wait(1, SC_NS);')
                cog.outl('    std::string outs (outport);')

                num_ports = len(top_p.outPorts)
                for port in top_p.outPorts:
                    if num_ports > 1:
                        cog.outl(f"    if (outs == \\"{port.name}\\"){{")
                        cog.outl(f"            singleton->{self.get_sysc_port_name(port)}->write(data);")
                        cog.outl("    }")
                    else:
                        cog.outl(f"    singleton->{self.get_sysc_port_name(port)}->write(data);")
                cog.outl('    return Py_None;')
                cog.outl("}")
        ]]]*/
        //[[[end]]]

        /*[[[cog
            if body_type is not PyInteractiveBody:
                if body_type is PyConstBody:
                    body = dill.loads(self._bodies[top_p.body].python.dillImpl)
                    val = body.eval()
                for port in top_p.outPorts:
                    port_type = self.load_port_type(port)
                    cog.outl(f"void {module_name}::set_{self.get_sysc_port_name(port)}(){{")
                    cog.outl(f"    if ({self.get_sysc_port_name(port)} != NULL){{")
                    if body_type is PyConstBody:
                        if port.name:
                            port_val = val[port.name]
                        else:
                            port_val = val
                        if port_val is not None:
                            cog.outl(f'        {self.get_sysc_port_name(port)}->nb_write("{port_type.pack(port_val).decode("ascii")}");')
                        else:
                            raise ValueError(f'None returned by constant node {top_p.name}.')
                    else:
                        if port.name:
                            cog.outl(f"        PyObject* pyRet = PyObject_GetAttrString(this->pyC,\\"{port.name}\\");")
                        else:
                            cog.outl(f"        PyObject* pyRet = this->pyC;")
                        cog.outl("        if (pyRet != Py_None){")
                        cog.outl(f"            PyObject* pyBits = PyObject_CallMethodObjArgs(this->type_{self.get_sysc_port_name(port)}, PyUnicode_FromString(\\"pack\\"), pyRet, NULL);")
                        cog.outl("             PyObject* pyErr = PyErr_Occurred();")
                        cog.outl("             if (pyErr != NULL) {")
                        cog.outl("                 PyErr_Print();")
                        cog.outl("                 PyErr_Clear();")
                        cog.outl("                 exit(-1);")
                        cog.outl("             }")
                        cog.outl(f"            char* bitsRet = PyBytes_AsString(pyBits);")
                        cog.outl(f"            {self.get_sysc_port_name(port)}->write(bitsRet);")
                        cog.outl("        }")
                    cog.outl("    }")
                    cog.outl("};")
        ]]]*/
        //[[[end]]]

        //[[[cog cog.outl(f'void {module_name}::body(){{') ]]]
        //[[[end]]]
            /*[[[cog
            if body_type is not PyInteractiveBody:
                cog.outl('while (true) {')
            ]]]*/
            //[[[end]]]
                /*[[[cog

                    if body_type is not PyConstBody:
                        if body_type is PyInteractiveBody:
                            cog.outl('this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"), this->pNode , NULL);')
                        else:
                            if top_p.inPorts:
                                args = [f'get_{self.get_sysc_port_name(port)}()' for port in top_p.inPorts]
                                cog.outl('this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"),' + ",".join(args) +' ,NULL);')
                            else:
                                cog.outl('this->pyC = PyObject_CallMethod(this->pBody, "eval", NULL);')
                        cog.outl("PyObject* pyErr = PyErr_Occurred();")
                        cog.outl("if (pyErr != NULL) {")
                        cog.outl("    if (PyErr_ExceptionMatches(this->pExit)) {")
                        cog.outl("        PyErr_Clear();")
                        cog.outl("        sc_stop();")
                        if body_type is not PyInteractiveBody:
                            cog.outl("        break;")
                        cog.outl("    } else {")
                        cog.outl("        PyErr_Print();")
                        cog.outl("        PyErr_Clear();")
                        cog.outl("        exit(-1);")
                        cog.outl("    }")
                        cog.outl("}")
                ]]]*/
                //[[[end]]]
                /*[[[cog
                    if body_type is not PyInteractiveBody:
                        if body_type is PyConstBody:
                            for port in top_p.outPorts:
                                cog.outl(f'set_{self.get_sysc_port_name(port)}();')
                        else:
                            cog.outl("if (this->pyC != Py_None) {")
                            for port in top_p.outPorts:
                                cog.outl(f'    set_{self.get_sysc_port_name(port)}();')
                            cog.outl("}")
                ]]]*/
                //[[[end]]]
            /*[[[cog
            if body_type is not PyInteractiveBody:
                cog.outl('    wait(1, SC_NS);')
                cog.outl('}')
            ]]]*/
            //[[[end]]]
        };

        //[[[cog cog.outl(f"int {module_name}::get_no_inputs() const") ]]]
        //[[[end]]]
        {
            return no_ins;
        };

        //[[[cog cog.outl(f"int {module_name}::get_no_outputs() const") ]]]
        //[[[end]]]
        {
            return no_outs;
        };
        """

        module_name = self.get_module_name(top_p)
        cpp_name = path.join(self.tempdir, f"{top_p.name}.cpp")
        with open(cpp_name, "wb") as out_file:
            out_file.write(cogify(cpp_tmpl, globals=dict(globals(), **locals())))
        return True

    def _get_cpp(self, top_p, after):
        """Get the C++ code containing the node's SystemC module after
        it has been built.

        Parameters
        ----------
        top_p
            capnp object describing the node.
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
            capnp object describing the node. Used to get the node's name.
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
            capnp object describing the node. Used to get the node's name.
        after : Coroutine
            Build process that needs to complete before the binary object
            is ready.

        Returns
        -------
        BuildArtifact
            The built binary object for the node.
        """
        return self._get_o(top_p.name, after)

    def pythonate(self, top_p):
        """Generates all the build outputs for this node.

        Parameters
        ----------
        top_p
            capnp object describing the node.

        Returns
        -------
        dict
            A map of strings to `BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects containing different
            parts of the node's SystemC implementation:

            - "cpp": the C++ file
            - "h": the header file
            - "py": the Python file (only exists if the node is not constant)
            - "o": the built binary object
        """
        body_class = self._bodies[top_p.body].which()
        if "python" in body_class:
            body = self._bodies[top_p.body].python.dillImpl
        if "interactive" in body_class:
            body = self._bodies[top_p.body].interactive.dillImpl
        body_type = type(dill.loads(body))
        make_cpp = self._make_cpp(top_p, body_type)
        cpp = self._get_cpp(top_p, after=make_cpp)
        make_h = self._make_h(top_p, body_type)
        h = self._get_h(top_p, after=make_h)
        if body_type is not PyConstBody:
            make_py = self._make_py(top_p, body)
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
