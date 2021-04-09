#include "pythonate_interactive_5.h"

Pythonate_Interactive_5_module* Pythonate_Interactive_5_module::singleton = nullptr;
Pythonate_Interactive_5_module::Pythonate_Interactive_5_module(sc_module_name name): sc_module(name) {
    if (singleton == nullptr) {
    singleton = this;
    } else {
    std::cerr << "attempted to construct multiple python for Pythonate_Interactive_5_module modules - not supported!" << std::endl;
    exit(-1);
    }
    no_ins = 3;
    no_outs = 1;
    const char* sc_module_name = "pythonate_interactive_5_module_sysc";
    PyImport_AddModule(sc_module_name);
    PyObject* sys_modules = PyImport_GetModuleDict();
    PyObject* module = PyInit_sysc();
    PyDict_SetItemString(sys_modules, sc_module_name, module);
    this->pName = PyUnicode_DecodeFSDefault("pythonate_interactive_5");
    this->pModule = PyImport_Import(this->pName);
    if (this->pModule == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import pythonate_interactive_5 python module." << std::endl;
    exit(-1);
    }
    this->pBody = PyObject_GetAttrString(this->pModule, "body");
    if (this->pBody == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import pythonate_interactive_5 python body." << std::endl;
    exit(-1);
    }
    this->pNode = PyObject_GetAttrString(this->pModule, "node");
    if (this->pBody == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import pythonate_interactive_5 python interactive node." << std::endl;
    exit(-1);
    }
    PyObject *runtimeModule = PyImport_Import(PyUnicode_DecodeFSDefault("deltalanguage.runtime"));
    if (runtimeModule == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import deltalanguage runtime in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    this->pExit = PyObject_GetAttrString(runtimeModule, "DeltaRuntimeExit");
    if (this->pExit == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import exit exception object from deltalanguage runtime in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    this->type_sysc_num = PyObject_GetAttrString(this->pModule, "sysc_num");
    if (this->type_sysc_num == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for in port num in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    sysc_num = NULL;
    this->type_sysc_val = PyObject_GetAttrString(this->pModule, "sysc_val");
    if (this->type_sysc_val == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for in port val in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    sysc_val = NULL;
    this->type_sysc_opt = PyObject_GetAttrString(this->pModule, "sysc_opt");
    if (this->type_sysc_opt == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for in port opt in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    sysc_opt = NULL;
    this->type_sysc_output = PyObject_GetAttrString(this->pModule, "sysc_output");
    if (this->type_sysc_output == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for out port output in pythonate_interactive_5." << std::endl;
    exit(-1);
    }
    sysc_output = NULL;
    Py_XDECREF(this->pName);
    Py_XDECREF(this->pModule);
    SC_THREAD(body);
}

PyMethodDef Pythonate_Interactive_5_module::SysCMethods[] = {
{"receive", sc_receive, METH_VARARGS, "Receives data from the systemC interface"},
{"send", sc_send, METH_VARARGS, "Sends data to the systemC interface"},
{NULL, NULL, 0, NULL}
};
PyModuleDef Pythonate_Interactive_5_module::SysCModule = {
PyModuleDef_HEAD_INIT, "pythonate_interactive_5_module_sysc", NULL, -1, SysCMethods,
NULL, NULL, NULL, NULL
};
PyObject* Pythonate_Interactive_5_module::PyInit_sysc(void)
{
std::cout << "Pythonate_Interactive_5_module::PyInit_sysc() called " << std::endl;
return PyModule_Create(&SysCModule);
}
PyObject* Pythonate_Interactive_5_module::sc_receive(PyObject *self, PyObject *args){
    const char * inport; 
    bool retval; 
sc_dt::sc_bv<32> bv_sysc_num;
sc_dt::sc_bv<32> bv_sysc_val;
sc_dt::sc_bv<32> bv_sysc_opt;
    if (!PyArg_ParseTuple(args, "s", &inport )) {
        std::cout << "sc_receive::ERROR" << std::endl;
        return NULL;
    }
    std::string ins (inport);
    if (ins == "num") {
      singleton->sysc_num->read(bv_sysc_num);
return PyObject_CallMethodObjArgs(singleton->type_sysc_num, PyUnicode_FromString("unpack"), PyBytes_FromStringAndSize(bv_sysc_num.to_string().c_str(), 32), NULL);
}
    if (ins == "val") {
      singleton->sysc_val->read(bv_sysc_val);
return PyObject_CallMethodObjArgs(singleton->type_sysc_val, PyUnicode_FromString("unpack"), PyBytes_FromStringAndSize(bv_sysc_val.to_string().c_str(), 32), NULL);
}
    if (ins == "opt") {
      retval = singleton->sysc_opt->nb_read(bv_sysc_opt);
      if (retval == false){
          return Py_None;
      }
return PyObject_CallMethodObjArgs(singleton->type_sysc_opt, PyUnicode_FromString("unpack"), PyBytes_FromStringAndSize(bv_sysc_opt.to_string().c_str(), 32), NULL);
}
    PyErr_SetString(PyExc_TypeError, "Unrecognized argument");
    return (PyObject *) NULL;
}
PyObject* Pythonate_Interactive_5_module::sc_send(PyObject *self, PyObject *args){
    const char * outport;
    const char * data;
    if (!PyArg_ParseTuple(args, "ss*", &outport, &data)) {
        std::cout << "sc_send::ERROR" << std::endl;
        return NULL;
    }
    singleton->wait(1, SC_NS);
    std::string outs (outport);
    singleton->sysc_output->write(data);
    return Py_None;
}


void Pythonate_Interactive_5_module::body(){
        this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"), this->pNode , NULL);
        PyObject* pyErr = PyErr_Occurred();
        if (pyErr != NULL) {
            if (PyErr_ExceptionMatches(this->pExit)) {
                PyErr_Clear();
                sc_stop();
            } else {
                PyErr_Print();
                PyErr_Clear();
                exit(-1);
            }
        }
};

int Pythonate_Interactive_5_module::get_no_inputs() const
{
    return no_ins;
};

int Pythonate_Interactive_5_module::get_no_outputs() const
{
    return no_outs;
};
