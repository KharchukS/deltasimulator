#include <iostream>
#include <systemc>
#include <limits>
#include <sstream>
#include <Python.h>
#include "dut.h"



using namespace std;
using namespace sc_core;
using namespace sc_dt;


int sc_main(__attribute__((unused)) int argc, __attribute__((unused)) char** argv) {
  sc_core::sc_report_handler::set_actions( "/IEEE_Std_1666/deprecated",
                                           sc_core::SC_DO_NOTHING );  

  Py_Initialize();

  sc_trace_file *Tf = nullptr;
  sc_clock clk("clk", sc_time(1, SC_NS));
  sc_signal<bool> rst; 

  Dut dut("Dut", Tf);
  dut.clk.bind(clk);
  dut.rst.bind(rst);
  rst.write(0);
  
  try {
    sc_start(1000, SC_NS);
    cout << "Completed!" << endl;
  } catch (const std::exception &exc){
    cout << "exiting on error" << endl;
    cerr << exc.what();
    Py_Finalize();
    throw;
  }
  Py_Finalize();
  return 0;
}
