// Verilated -*- SystemC -*-
// DESCRIPTION: Verilator output: Primary design header
//
// This header should be included by all source files instantiating the design.
// The class here is then constructed to instantiate the design.
// See the Verilator manual for examples.

#ifndef _VCOUNTER1_1_H_
#define _VCOUNTER1_1_H_  // guard

#include "systemc.h"
#include "verilated_sc.h"
#include "verilated.h"

class Vcounter1_1__Syms;

//----------

SC_MODULE(Vcounter1_1) {
  public:
    
    // PORTS
    // The application code writes and reads these signals to
    // propagate new values into/out from the Verilated model.
    sc_in<sc_bv<32> > i1_in_data;
    sc_in<sc_bv<1> > i1_in_valid;
    sc_out<sc_bv<1> > i1_in_ready;
    sc_out<sc_bv<32> > o1_out_data;
    sc_out<sc_bv<1> > o1_out_valid;
    sc_in<sc_bv<1> > o1_out_ready;
    sc_in<sc_bv<1> > sys_clk;
    sc_in<sc_bv<1> > sys_rst;
    
    // LOCAL SIGNALS
    // Internals; generally not touched by application code
    WData/*999:0*/ counter1_1__DOT__counter[32];
    IData/*31:0*/ counter1_1__DOT__mem1[100];
    IData/*31:0*/ counter1_1__DOT__mem2[100];
    
    // LOCAL VARIABLES
    // Internals; generally not touched by application code
    CData/*0:0*/ __Vcellinp__counter1_1__sys_clk;
    CData/*0:0*/ __Vcellinp__counter1_1__sys_rst;
    CData/*0:0*/ __Vcellinp__counter1_1__o1_out_ready;
    CData/*0:0*/ __Vcellout__counter1_1__o1_out_valid;
    CData/*0:0*/ __Vcellout__counter1_1__i1_in_ready;
    CData/*0:0*/ __Vclklast__TOP____Vcellinp__counter1_1__sys_clk;
    IData/*31:0*/ __Vcellout__counter1_1__o1_out_data;
    IData/*31:0*/ __Vcellinp__counter1_1__i1_in_data;
    
    // INTERNAL VARIABLES
    // Internals; generally not touched by application code
    Vcounter1_1__Syms* __VlSymsp;  // Symbol table
    
    // PARAMETERS
    // Parameters marked /*verilator public*/ for use by application code
    
    // CONSTRUCTORS
  private:
    VL_UNCOPYABLE(Vcounter1_1);  ///< Copying not allowed
  public:
    SC_CTOR(Vcounter1_1);
    virtual ~Vcounter1_1();
    
    // API METHODS
  private:
    void eval();
  public:
    void final();
    
    // INTERNAL METHODS
  private:
    static void _eval_initial_loop(Vcounter1_1__Syms* __restrict vlSymsp);
  public:
    void __Vconfigure(Vcounter1_1__Syms* symsp, bool first);
  private:
    static QData _change_request(Vcounter1_1__Syms* __restrict vlSymsp);
  public:
    static void _combo__TOP__2(Vcounter1_1__Syms* __restrict vlSymsp);
    static void _combo__TOP__5(Vcounter1_1__Syms* __restrict vlSymsp);
  private:
    void _ctor_var_reset() VL_ATTR_COLD;
  public:
    static void _eval(Vcounter1_1__Syms* __restrict vlSymsp);
  private:
#ifdef VL_DEBUG
    void _eval_debug_assertions();
#endif  // VL_DEBUG
  public:
    static void _eval_initial(Vcounter1_1__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _eval_settle(Vcounter1_1__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _initial__TOP__1(Vcounter1_1__Syms* __restrict vlSymsp) VL_ATTR_COLD;
    static void _sequent__TOP__4(Vcounter1_1__Syms* __restrict vlSymsp);
    static void _settle__TOP__3(Vcounter1_1__Syms* __restrict vlSymsp) VL_ATTR_COLD;
} VL_ATTR_ALIGNED(128);

#endif  // guard
