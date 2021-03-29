#ifndef __ADD_2_MODULE__
#define __ADD_2_MODULE__

#include <string>
#include <systemc>
using namespace sc_core;
#include "Python.h"

class Add_2_module : public sc_module
{
private:
    PyObject *pBody, *pName, *pModule, *pyC, *pExit;
    uint64_t no_ins, no_outs;
    PyObject* type_sysc_a;
    PyObject* get_sysc_a();
    sc_dt::sc_bv<32> bits_sysc_a;
    PyObject* type_sysc_b;
    PyObject* get_sysc_b();
    sc_dt::sc_bv<32> bits_sysc_b;
    PyObject* type_sysc_return;
    sc_dt::sc_bv<32> bits_sysc_return;
    void set_sysc_return();
public:
    uint64_t no_inputs, no_outputs;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_a;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_b;
    sc_fifo<sc_dt::sc_bv<32>>* sysc_return;
    int get_no_inputs() const;
    int get_no_outputs() const;
    void body();
    SC_HAS_PROCESS(Add_2_module);
    Add_2_module(sc_module_name name);
};
#endif
