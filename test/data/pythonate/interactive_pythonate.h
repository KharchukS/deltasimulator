#ifndef __PYTHONATE_INTERACTIVE_5_MODULE__
#define __PYTHONATE_INTERACTIVE_5_MODULE__

#include <string>
#include <systemc>
using namespace sc_core;
#include "Python.h"

class Pythonate_Interactive_5_module : public sc_module
{
private:
    PyObject *pBody, *pName, *pModule, *pyC, *pExit;
    PyObject *runtimeModule, *pNode;
    static PyObject* sc_receive(PyObject *self, PyObject *args);
    static PyObject* sc_send(PyObject *self, PyObject *args);
    static PyObject* PyInit_sysc(void);
    static PyMethodDef SysCMethods[];
    static PyModuleDef SysCModule;
    static Pythonate_Interactive_5_module* singleton;
    void init();
    void store();
    void run();
    uint64_t no_ins, no_outs;
    PyObject* type_sysc_num;
    PyObject* get_sysc_num();
    sc_dt::sc_bv<32> bits_sysc_num;
    PyObject* type_sysc_val;
    PyObject* get_sysc_val();
    sc_dt::sc_bv<32> bits_sysc_val;
    PyObject* type_sysc_opt;
    PyObject* get_sysc_opt();
    sc_dt::sc_bv<32> bits_sysc_opt;
    PyObject* type_sysc_output;
    sc_dt::sc_bv<32> bits_sysc_output;
    void set_sysc_output();
public:
    uint64_t no_inputs, no_outputs;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_num;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_val;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_opt;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_output;
    int get_no_inputs() const;
    int get_no_outputs() const;
    void body();
    SC_HAS_PROCESS(Pythonate_Interactive_5_module);
    Pythonate_Interactive_5_module(sc_module_name name);
};
#endif
