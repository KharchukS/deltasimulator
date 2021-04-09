#include "add_2.h"

Add_2_module::Add_2_module(sc_module_name name): sc_module(name) {
    no_ins = 2;
    no_outs = 1;
    this->pName = PyUnicode_DecodeFSDefault("add_2");
    this->pModule = PyImport_Import(this->pName);
    if (this->pModule == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import add_2 python module." << std::endl;
    exit(-1);
    }
    this->pBody = PyObject_GetAttrString(this->pModule, "body");
    if (this->pBody == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import add_2 python body." << std::endl;
    exit(-1);
    }
    PyObject *runtimeModule = PyImport_Import(PyUnicode_DecodeFSDefault("deltalanguage.runtime"));
    if (runtimeModule == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import deltalanguage runtime in add_2." << std::endl;
    exit(-1);
    }
    this->pExit = PyObject_GetAttrString(runtimeModule, "DeltaRuntimeExit");
    if (this->pExit == NULL) {
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import exit exception object from deltalanguage runtime in add_2." << std::endl;
    exit(-1);
    }
    this->type_sysc_a = PyObject_GetAttrString(this->pModule, "sysc_a");
    if (this->type_sysc_a == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for in port a in add_2." << std::endl;
    exit(-1);
    }
    sysc_a = NULL;
    this->type_sysc_b = PyObject_GetAttrString(this->pModule, "sysc_b");
    if (this->type_sysc_b == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for in port b in add_2." << std::endl;
    exit(-1);
    }
    sysc_b = NULL;
    this->type_sysc_output = PyObject_GetAttrString(this->pModule, "sysc_output");
    if (this->type_sysc_output == NULL){
    if (PyErr_Occurred()) PyErr_Print();
    std::cout << "failed to import type for out port output in add_2." << std::endl;
    exit(-1);
    }
    sysc_output = NULL;
    Py_XDECREF(this->pName);
    Py_XDECREF(this->pModule);
    SC_THREAD(body);
}

PyObject* Add_2_module::get_sysc_a(){
    if (sysc_a == NULL) return Py_None;
    bits_sysc_a = sysc_a->read();
    return PyObject_CallMethodObjArgs(this->type_sysc_a, PyUnicode_FromString("unpack"), PyBytes_FromStringAndSize(bits_sysc_a.to_string().c_str(), 32), NULL);
};
PyObject* Add_2_module::get_sysc_b(){
    if (sysc_b == NULL) return Py_None;
    bits_sysc_b = sysc_b->read();
    return PyObject_CallMethodObjArgs(this->type_sysc_b, PyUnicode_FromString("unpack"), PyBytes_FromStringAndSize(bits_sysc_b.to_string().c_str(), 32), NULL);
};

void Add_2_module::set_sysc_output(){
    if (sysc_output != NULL){
        PyObject* pyRet = this->pyC;
        if (pyRet != Py_None){
            PyObject* pyBits = PyObject_CallMethodObjArgs(this->type_sysc_output, PyUnicode_FromString("pack"), pyRet, NULL);
             PyObject* pyErr = PyErr_Occurred();
             if (pyErr != NULL) {
                 PyErr_Print();
                 PyErr_Clear();
                 exit(-1);
             }
            char* bitsRet = PyBytes_AsString(pyBits);
            sysc_output->write(bitsRet);
        }
    }
};

void Add_2_module::body(){
    while (true) {
        this->pyC = PyObject_CallMethodObjArgs(this->pBody, PyUnicode_FromString("eval"),get_sysc_a(),get_sysc_b() ,NULL);
        PyObject* pyErr = PyErr_Occurred();
        if (pyErr != NULL) {
            if (PyErr_ExceptionMatches(this->pExit)) {
                PyErr_Clear();
                sc_stop();
                break;
            } else {
                PyErr_Print();
                PyErr_Clear();
                exit(-1);
            }
        }
        if (this->pyC != Py_None) {
            set_sysc_output();
        }
        wait(1, SC_NS);
    }
};

int Add_2_module::get_no_inputs() const
{
    return no_ins;
};

int Add_2_module::get_no_outputs() const
{
    return no_outs;
};
