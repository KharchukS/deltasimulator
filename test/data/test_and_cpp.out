
#include <systemc>
#include <iostream>
#include <string>
#include "test_and.h"
#include "Python.h"
using namespace sc_core;
using namespace std;
int sc_main(int argc, char* argv[]) {
    Py_UnbufferedStdioFlag = 1;
    Py_Initialize();
    // Adds required components: trace, clock, reset
    sc_trace_file *Tf = sc_create_vcd_trace_file("test_and");
    Test_And test_and("test_and", Tf);
    sc_clock clk("clk", sc_time(1, SC_NS)); sc_trace(Tf, clk, "clk");
    sc_signal<bool> rst; sc_trace(Tf, rst, "rst");
    rst.write(0);
    test_and.clk.bind(clk);
    test_and.rst.bind(rst);

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
