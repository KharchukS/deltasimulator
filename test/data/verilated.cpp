// Verilated -*- SystemC -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcounter1_1.h for the primary calling header

#include "Vcounter1_1.h"
#include "Vcounter1_1__Syms.h"


//--------------------
// STATIC VARIABLES


//--------------------

VL_SC_CTOR_IMP(Vcounter1_1)
#if (SYSTEMC_VERSION>20011000)
    : i1_in_data("i1_in_data"), i1_in_valid("i1_in_valid"), 
      i1_in_ready("i1_in_ready"), o1_out_data("o1_out_data"), 
      o1_out_valid("o1_out_valid"), o1_out_ready("o1_out_ready"), 
      sys_clk("sys_clk"), sys_rst("sys_rst")
#endif
 {
    Vcounter1_1__Syms* __restrict vlSymsp = __VlSymsp = new Vcounter1_1__Syms(this, name());
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Sensitivities on all clocks and combo inputs
    SC_METHOD(eval);
    sensitive << i1_in_data;
    sensitive << o1_out_ready;
    sensitive << sys_clk;
    sensitive << sys_rst;
    
    // Reset internal values
    
    // Reset structure values
    _ctor_var_reset();
}

void Vcounter1_1::__Vconfigure(Vcounter1_1__Syms* vlSymsp, bool first) {
    if (0 && first) {}  // Prevent unused
    this->__VlSymsp = vlSymsp;
}

Vcounter1_1::~Vcounter1_1() {
    delete __VlSymsp; __VlSymsp=NULL;
}

//--------------------


void Vcounter1_1::eval() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcounter1_1::eval\n"); );
    Vcounter1_1__Syms* __restrict vlSymsp = this->__VlSymsp;  // Setup global symbol table
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
#ifdef VL_DEBUG
    // Debug assertions
    _eval_debug_assertions();
#endif  // VL_DEBUG
    // Initialize
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) _eval_initial_loop(vlSymsp);
    // Evaluate till stable
    int __VclockLoop = 0;
    QData __Vchange = 1;
    do {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Clock loop\n"););
        _eval(vlSymsp);
        if (VL_UNLIKELY(++__VclockLoop > 100)) {
            // About to fail, so enable debug to see what's not settling.
            // Note you must run make with OPT=-DVL_DEBUG for debug prints.
            int __Vsaved_debug = Verilated::debug();
            Verilated::debug(1);
            __Vchange = _change_request(vlSymsp);
            Verilated::debug(__Vsaved_debug);
            VL_FATAL_MT("counter1_1", 2, "",
                "Verilated model didn't converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

void Vcounter1_1::_eval_initial_loop(Vcounter1_1__Syms* __restrict vlSymsp) {
    vlSymsp->__Vm_didInit = true;
    _eval_initial(vlSymsp);
    // Evaluate till stable
    int __VclockLoop = 0;
    QData __Vchange = 1;
    do {
        _eval_settle(vlSymsp);
        _eval(vlSymsp);
        if (VL_UNLIKELY(++__VclockLoop > 100)) {
            // About to fail, so enable debug to see what's not settling.
            // Note you must run make with OPT=-DVL_DEBUG for debug prints.
            int __Vsaved_debug = Verilated::debug();
            Verilated::debug(1);
            __Vchange = _change_request(vlSymsp);
            Verilated::debug(__Vsaved_debug);
            VL_FATAL_MT("counter1_1", 2, "",
                "Verilated model didn't DC converge\n"
                "- See DIDNOTCONVERGE in the Verilator manual");
        } else {
            __Vchange = _change_request(vlSymsp);
        }
    } while (VL_UNLIKELY(__Vchange));
}

//--------------------
// Internal Methods

void Vcounter1_1::_initial__TOP__1(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_initial__TOP__1\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    WData/*95:0*/ __Vtemp1[3];
    WData/*95:0*/ __Vtemp2[3];
    // Body
    __Vtemp1[0U] = 0x696e6974U;
    __Vtemp1[1U] = 0x656d312eU;
    __Vtemp1[2U] = 0x6dU;
    VL_READMEM_W(true,32,100, 0,3, __Vtemp1, vlTOPp->counter1_1__DOT__mem1
                 ,0,~0);
    __Vtemp2[0U] = 0x696e6974U;
    __Vtemp2[1U] = 0x656d322eU;
    __Vtemp2[2U] = 0x6dU;
    VL_READMEM_W(true,32,100, 0,3, __Vtemp2, vlTOPp->counter1_1__DOT__mem2
                 ,0,~0);
    vlTOPp->counter1_1__DOT__counter[0U] = 0U;
    vlTOPp->counter1_1__DOT__counter[1U] = 0U;
    vlTOPp->counter1_1__DOT__counter[2U] = 0U;
    vlTOPp->counter1_1__DOT__counter[3U] = 0U;
    vlTOPp->counter1_1__DOT__counter[4U] = 0U;
    vlTOPp->counter1_1__DOT__counter[5U] = 0U;
    vlTOPp->counter1_1__DOT__counter[6U] = 0U;
    vlTOPp->counter1_1__DOT__counter[7U] = 0U;
    vlTOPp->counter1_1__DOT__counter[8U] = 0U;
    vlTOPp->counter1_1__DOT__counter[9U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xaU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xbU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xcU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xdU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xeU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0xfU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x10U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x11U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x12U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x13U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x14U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x15U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x16U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x17U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x18U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x19U] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1aU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1bU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1cU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1dU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1eU] = 0U;
    vlTOPp->counter1_1__DOT__counter[0x1fU] = 0U;
}

VL_INLINE_OPT void Vcounter1_1::_combo__TOP__2(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_combo__TOP__2\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    VL_ASSIGN_ISW(32,vlTOPp->__Vcellinp__counter1_1__i1_in_data, vlTOPp->i1_in_data);
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__o1_out_ready, vlTOPp->o1_out_ready);
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__sys_clk, vlTOPp->sys_clk);
}

void Vcounter1_1::_settle__TOP__3(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_settle__TOP__3\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    WData/*1023:0*/ __Vtemp3[32];
    // Body
    VL_ASSIGN_ISW(32,vlTOPp->__Vcellinp__counter1_1__i1_in_data, vlTOPp->i1_in_data);
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__o1_out_ready, vlTOPp->o1_out_ready);
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__sys_clk, vlTOPp->sys_clk);
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__sys_rst, vlTOPp->sys_rst);
    vlTOPp->__Vcellout__counter1_1__i1_in_ready = 0U;
    __Vtemp3[0U] = 5U;
    __Vtemp3[1U] = 0U;
    __Vtemp3[2U] = 0U;
    __Vtemp3[3U] = 0U;
    __Vtemp3[4U] = 0U;
    __Vtemp3[5U] = 0U;
    __Vtemp3[6U] = 0U;
    __Vtemp3[7U] = 0U;
    __Vtemp3[8U] = 0U;
    __Vtemp3[9U] = 0U;
    __Vtemp3[0xaU] = 0U;
    __Vtemp3[0xbU] = 0U;
    __Vtemp3[0xcU] = 0U;
    __Vtemp3[0xdU] = 0U;
    __Vtemp3[0xeU] = 0U;
    __Vtemp3[0xfU] = 0U;
    __Vtemp3[0x10U] = 0U;
    __Vtemp3[0x11U] = 0U;
    __Vtemp3[0x12U] = 0U;
    __Vtemp3[0x13U] = 0U;
    __Vtemp3[0x14U] = 0U;
    __Vtemp3[0x15U] = 0U;
    __Vtemp3[0x16U] = 0U;
    __Vtemp3[0x17U] = 0U;
    __Vtemp3[0x18U] = 0U;
    __Vtemp3[0x19U] = 0U;
    __Vtemp3[0x1aU] = 0U;
    __Vtemp3[0x1bU] = 0U;
    __Vtemp3[0x1cU] = 0U;
    __Vtemp3[0x1dU] = 0U;
    __Vtemp3[0x1eU] = 0U;
    __Vtemp3[0x1fU] = 0U;
    if (VL_LTE_W(32, __Vtemp3, vlTOPp->counter1_1__DOT__counter)) {
        vlTOPp->__Vcellout__counter1_1__i1_in_ready = 1U;
    }
    vlTOPp->__Vcellout__counter1_1__o1_out_valid = 0U;
    if (vlTOPp->__Vcellinp__counter1_1__o1_out_ready) {
        vlTOPp->__Vcellout__counter1_1__o1_out_valid 
            = (0U == ((((((((((((((((((((((((((((((
                                                   ((0xaU 
                                                     ^ 
                                                     vlTOPp->counter1_1__DOT__counter[0U]) 
                                                    | vlTOPp->counter1_1__DOT__counter[1U]) 
                                                   | vlTOPp->counter1_1__DOT__counter[2U]) 
                                                  | vlTOPp->counter1_1__DOT__counter[3U]) 
                                                 | vlTOPp->counter1_1__DOT__counter[4U]) 
                                                | vlTOPp->counter1_1__DOT__counter[5U]) 
                                               | vlTOPp->counter1_1__DOT__counter[6U]) 
                                              | vlTOPp->counter1_1__DOT__counter[7U]) 
                                             | vlTOPp->counter1_1__DOT__counter[8U]) 
                                            | vlTOPp->counter1_1__DOT__counter[9U]) 
                                           | vlTOPp->counter1_1__DOT__counter[0xaU]) 
                                          | vlTOPp->counter1_1__DOT__counter[0xbU]) 
                                         | vlTOPp->counter1_1__DOT__counter[0xcU]) 
                                        | vlTOPp->counter1_1__DOT__counter[0xdU]) 
                                       | vlTOPp->counter1_1__DOT__counter[0xeU]) 
                                      | vlTOPp->counter1_1__DOT__counter[0xfU]) 
                                     | vlTOPp->counter1_1__DOT__counter[0x10U]) 
                                    | vlTOPp->counter1_1__DOT__counter[0x11U]) 
                                   | vlTOPp->counter1_1__DOT__counter[0x12U]) 
                                  | vlTOPp->counter1_1__DOT__counter[0x13U]) 
                                 | vlTOPp->counter1_1__DOT__counter[0x14U]) 
                                | vlTOPp->counter1_1__DOT__counter[0x15U]) 
                               | vlTOPp->counter1_1__DOT__counter[0x16U]) 
                              | vlTOPp->counter1_1__DOT__counter[0x17U]) 
                             | vlTOPp->counter1_1__DOT__counter[0x18U]) 
                            | vlTOPp->counter1_1__DOT__counter[0x19U]) 
                           | vlTOPp->counter1_1__DOT__counter[0x1aU]) 
                          | vlTOPp->counter1_1__DOT__counter[0x1bU]) 
                         | vlTOPp->counter1_1__DOT__counter[0x1cU]) 
                        | vlTOPp->counter1_1__DOT__counter[0x1dU]) 
                       | vlTOPp->counter1_1__DOT__counter[0x1eU]) 
                      | vlTOPp->counter1_1__DOT__counter[0x1fU]));
    }
    vlTOPp->__Vcellout__counter1_1__o1_out_data = 0U;
    if (vlTOPp->__Vcellinp__counter1_1__o1_out_ready) {
        if ((0U == ((((((((((((((((((((((((((((((((0xaU 
                                                   ^ 
                                                   vlTOPp->counter1_1__DOT__counter[0U]) 
                                                  | vlTOPp->counter1_1__DOT__counter[1U]) 
                                                 | vlTOPp->counter1_1__DOT__counter[2U]) 
                                                | vlTOPp->counter1_1__DOT__counter[3U]) 
                                               | vlTOPp->counter1_1__DOT__counter[4U]) 
                                              | vlTOPp->counter1_1__DOT__counter[5U]) 
                                             | vlTOPp->counter1_1__DOT__counter[6U]) 
                                            | vlTOPp->counter1_1__DOT__counter[7U]) 
                                           | vlTOPp->counter1_1__DOT__counter[8U]) 
                                          | vlTOPp->counter1_1__DOT__counter[9U]) 
                                         | vlTOPp->counter1_1__DOT__counter[0xaU]) 
                                        | vlTOPp->counter1_1__DOT__counter[0xbU]) 
                                       | vlTOPp->counter1_1__DOT__counter[0xcU]) 
                                      | vlTOPp->counter1_1__DOT__counter[0xdU]) 
                                     | vlTOPp->counter1_1__DOT__counter[0xeU]) 
                                    | vlTOPp->counter1_1__DOT__counter[0xfU]) 
                                   | vlTOPp->counter1_1__DOT__counter[0x10U]) 
                                  | vlTOPp->counter1_1__DOT__counter[0x11U]) 
                                 | vlTOPp->counter1_1__DOT__counter[0x12U]) 
                                | vlTOPp->counter1_1__DOT__counter[0x13U]) 
                               | vlTOPp->counter1_1__DOT__counter[0x14U]) 
                              | vlTOPp->counter1_1__DOT__counter[0x15U]) 
                             | vlTOPp->counter1_1__DOT__counter[0x16U]) 
                            | vlTOPp->counter1_1__DOT__counter[0x17U]) 
                           | vlTOPp->counter1_1__DOT__counter[0x18U]) 
                          | vlTOPp->counter1_1__DOT__counter[0x19U]) 
                         | vlTOPp->counter1_1__DOT__counter[0x1aU]) 
                        | vlTOPp->counter1_1__DOT__counter[0x1bU]) 
                       | vlTOPp->counter1_1__DOT__counter[0x1cU]) 
                      | vlTOPp->counter1_1__DOT__counter[0x1dU]) 
                     | vlTOPp->counter1_1__DOT__counter[0x1eU]) 
                    | vlTOPp->counter1_1__DOT__counter[0x1fU]))) {
            vlTOPp->__Vcellout__counter1_1__o1_out_data 
                = (vlTOPp->counter1_1__DOT__counter[0U] 
                   + vlTOPp->__Vcellinp__counter1_1__i1_in_data);
        }
    }
    VL_ASSIGN_SWI(1,vlTOPp->i1_in_ready, vlTOPp->__Vcellout__counter1_1__i1_in_ready);
    VL_ASSIGN_SWI(1,vlTOPp->o1_out_valid, vlTOPp->__Vcellout__counter1_1__o1_out_valid);
    VL_ASSIGN_SWI(32,vlTOPp->o1_out_data, vlTOPp->__Vcellout__counter1_1__o1_out_data);
}

VL_INLINE_OPT void Vcounter1_1::_sequent__TOP__4(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_sequent__TOP__4\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Variables
    WData/*1023:0*/ __Vtemp8[32];
    WData/*1023:0*/ __Vtemp9[32];
    WData/*1023:0*/ __Vtemp10[32];
    // Body
    __Vtemp8[0U] = 1U;
    __Vtemp8[1U] = 0U;
    __Vtemp8[2U] = 0U;
    __Vtemp8[3U] = 0U;
    __Vtemp8[4U] = 0U;
    __Vtemp8[5U] = 0U;
    __Vtemp8[6U] = 0U;
    __Vtemp8[7U] = 0U;
    __Vtemp8[8U] = 0U;
    __Vtemp8[9U] = 0U;
    __Vtemp8[0xaU] = 0U;
    __Vtemp8[0xbU] = 0U;
    __Vtemp8[0xcU] = 0U;
    __Vtemp8[0xdU] = 0U;
    __Vtemp8[0xeU] = 0U;
    __Vtemp8[0xfU] = 0U;
    __Vtemp8[0x10U] = 0U;
    __Vtemp8[0x11U] = 0U;
    __Vtemp8[0x12U] = 0U;
    __Vtemp8[0x13U] = 0U;
    __Vtemp8[0x14U] = 0U;
    __Vtemp8[0x15U] = 0U;
    __Vtemp8[0x16U] = 0U;
    __Vtemp8[0x17U] = 0U;
    __Vtemp8[0x18U] = 0U;
    __Vtemp8[0x19U] = 0U;
    __Vtemp8[0x1aU] = 0U;
    __Vtemp8[0x1bU] = 0U;
    __Vtemp8[0x1cU] = 0U;
    __Vtemp8[0x1dU] = 0U;
    __Vtemp8[0x1eU] = 0U;
    __Vtemp8[0x1fU] = 0U;
    VL_ADD_W(32, __Vtemp9, __Vtemp8, vlTOPp->counter1_1__DOT__counter);
    vlTOPp->counter1_1__DOT__counter[0U] = __Vtemp9[0U];
    vlTOPp->counter1_1__DOT__counter[1U] = __Vtemp9[1U];
    vlTOPp->counter1_1__DOT__counter[2U] = __Vtemp9[2U];
    vlTOPp->counter1_1__DOT__counter[3U] = __Vtemp9[3U];
    vlTOPp->counter1_1__DOT__counter[4U] = __Vtemp9[4U];
    vlTOPp->counter1_1__DOT__counter[5U] = __Vtemp9[5U];
    vlTOPp->counter1_1__DOT__counter[6U] = __Vtemp9[6U];
    vlTOPp->counter1_1__DOT__counter[7U] = __Vtemp9[7U];
    vlTOPp->counter1_1__DOT__counter[8U] = __Vtemp9[8U];
    vlTOPp->counter1_1__DOT__counter[9U] = __Vtemp9[9U];
    vlTOPp->counter1_1__DOT__counter[0xaU] = __Vtemp9[0xaU];
    vlTOPp->counter1_1__DOT__counter[0xbU] = __Vtemp9[0xbU];
    vlTOPp->counter1_1__DOT__counter[0xcU] = __Vtemp9[0xcU];
    vlTOPp->counter1_1__DOT__counter[0xdU] = __Vtemp9[0xdU];
    vlTOPp->counter1_1__DOT__counter[0xeU] = __Vtemp9[0xeU];
    vlTOPp->counter1_1__DOT__counter[0xfU] = __Vtemp9[0xfU];
    vlTOPp->counter1_1__DOT__counter[0x10U] = __Vtemp9[0x10U];
    vlTOPp->counter1_1__DOT__counter[0x11U] = __Vtemp9[0x11U];
    vlTOPp->counter1_1__DOT__counter[0x12U] = __Vtemp9[0x12U];
    vlTOPp->counter1_1__DOT__counter[0x13U] = __Vtemp9[0x13U];
    vlTOPp->counter1_1__DOT__counter[0x14U] = __Vtemp9[0x14U];
    vlTOPp->counter1_1__DOT__counter[0x15U] = __Vtemp9[0x15U];
    vlTOPp->counter1_1__DOT__counter[0x16U] = __Vtemp9[0x16U];
    vlTOPp->counter1_1__DOT__counter[0x17U] = __Vtemp9[0x17U];
    vlTOPp->counter1_1__DOT__counter[0x18U] = __Vtemp9[0x18U];
    vlTOPp->counter1_1__DOT__counter[0x19U] = __Vtemp9[0x19U];
    vlTOPp->counter1_1__DOT__counter[0x1aU] = __Vtemp9[0x1aU];
    vlTOPp->counter1_1__DOT__counter[0x1bU] = __Vtemp9[0x1bU];
    vlTOPp->counter1_1__DOT__counter[0x1cU] = __Vtemp9[0x1cU];
    vlTOPp->counter1_1__DOT__counter[0x1dU] = __Vtemp9[0x1dU];
    vlTOPp->counter1_1__DOT__counter[0x1eU] = __Vtemp9[0x1eU];
    vlTOPp->counter1_1__DOT__counter[0x1fU] = (0xffU 
                                               & __Vtemp9[0x1fU]);
    if (vlTOPp->__Vcellinp__counter1_1__sys_rst) {
        vlTOPp->counter1_1__DOT__counter[0U] = 0U;
        vlTOPp->counter1_1__DOT__counter[1U] = 0U;
        vlTOPp->counter1_1__DOT__counter[2U] = 0U;
        vlTOPp->counter1_1__DOT__counter[3U] = 0U;
        vlTOPp->counter1_1__DOT__counter[4U] = 0U;
        vlTOPp->counter1_1__DOT__counter[5U] = 0U;
        vlTOPp->counter1_1__DOT__counter[6U] = 0U;
        vlTOPp->counter1_1__DOT__counter[7U] = 0U;
        vlTOPp->counter1_1__DOT__counter[8U] = 0U;
        vlTOPp->counter1_1__DOT__counter[9U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xaU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xbU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xcU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xdU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xeU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0xfU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x10U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x11U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x12U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x13U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x14U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x15U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x16U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x17U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x18U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x19U] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1aU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1bU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1cU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1dU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1eU] = 0U;
        vlTOPp->counter1_1__DOT__counter[0x1fU] = 0U;
    }
    vlTOPp->__Vcellout__counter1_1__i1_in_ready = 0U;
    __Vtemp10[0U] = 5U;
    __Vtemp10[1U] = 0U;
    __Vtemp10[2U] = 0U;
    __Vtemp10[3U] = 0U;
    __Vtemp10[4U] = 0U;
    __Vtemp10[5U] = 0U;
    __Vtemp10[6U] = 0U;
    __Vtemp10[7U] = 0U;
    __Vtemp10[8U] = 0U;
    __Vtemp10[9U] = 0U;
    __Vtemp10[0xaU] = 0U;
    __Vtemp10[0xbU] = 0U;
    __Vtemp10[0xcU] = 0U;
    __Vtemp10[0xdU] = 0U;
    __Vtemp10[0xeU] = 0U;
    __Vtemp10[0xfU] = 0U;
    __Vtemp10[0x10U] = 0U;
    __Vtemp10[0x11U] = 0U;
    __Vtemp10[0x12U] = 0U;
    __Vtemp10[0x13U] = 0U;
    __Vtemp10[0x14U] = 0U;
    __Vtemp10[0x15U] = 0U;
    __Vtemp10[0x16U] = 0U;
    __Vtemp10[0x17U] = 0U;
    __Vtemp10[0x18U] = 0U;
    __Vtemp10[0x19U] = 0U;
    __Vtemp10[0x1aU] = 0U;
    __Vtemp10[0x1bU] = 0U;
    __Vtemp10[0x1cU] = 0U;
    __Vtemp10[0x1dU] = 0U;
    __Vtemp10[0x1eU] = 0U;
    __Vtemp10[0x1fU] = 0U;
    if (VL_LTE_W(32, __Vtemp10, vlTOPp->counter1_1__DOT__counter)) {
        vlTOPp->__Vcellout__counter1_1__i1_in_ready = 1U;
    }
    VL_ASSIGN_SWI(1,vlTOPp->i1_in_ready, vlTOPp->__Vcellout__counter1_1__i1_in_ready);
}

VL_INLINE_OPT void Vcounter1_1::_combo__TOP__5(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_combo__TOP__5\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    VL_ASSIGN_ISW(1,vlTOPp->__Vcellinp__counter1_1__sys_rst, vlTOPp->sys_rst);
    vlTOPp->__Vcellout__counter1_1__o1_out_valid = 0U;
    if (vlTOPp->__Vcellinp__counter1_1__o1_out_ready) {
        vlTOPp->__Vcellout__counter1_1__o1_out_valid 
            = (0U == ((((((((((((((((((((((((((((((
                                                   ((0xaU 
                                                     ^ 
                                                     vlTOPp->counter1_1__DOT__counter[0U]) 
                                                    | vlTOPp->counter1_1__DOT__counter[1U]) 
                                                   | vlTOPp->counter1_1__DOT__counter[2U]) 
                                                  | vlTOPp->counter1_1__DOT__counter[3U]) 
                                                 | vlTOPp->counter1_1__DOT__counter[4U]) 
                                                | vlTOPp->counter1_1__DOT__counter[5U]) 
                                               | vlTOPp->counter1_1__DOT__counter[6U]) 
                                              | vlTOPp->counter1_1__DOT__counter[7U]) 
                                             | vlTOPp->counter1_1__DOT__counter[8U]) 
                                            | vlTOPp->counter1_1__DOT__counter[9U]) 
                                           | vlTOPp->counter1_1__DOT__counter[0xaU]) 
                                          | vlTOPp->counter1_1__DOT__counter[0xbU]) 
                                         | vlTOPp->counter1_1__DOT__counter[0xcU]) 
                                        | vlTOPp->counter1_1__DOT__counter[0xdU]) 
                                       | vlTOPp->counter1_1__DOT__counter[0xeU]) 
                                      | vlTOPp->counter1_1__DOT__counter[0xfU]) 
                                     | vlTOPp->counter1_1__DOT__counter[0x10U]) 
                                    | vlTOPp->counter1_1__DOT__counter[0x11U]) 
                                   | vlTOPp->counter1_1__DOT__counter[0x12U]) 
                                  | vlTOPp->counter1_1__DOT__counter[0x13U]) 
                                 | vlTOPp->counter1_1__DOT__counter[0x14U]) 
                                | vlTOPp->counter1_1__DOT__counter[0x15U]) 
                               | vlTOPp->counter1_1__DOT__counter[0x16U]) 
                              | vlTOPp->counter1_1__DOT__counter[0x17U]) 
                             | vlTOPp->counter1_1__DOT__counter[0x18U]) 
                            | vlTOPp->counter1_1__DOT__counter[0x19U]) 
                           | vlTOPp->counter1_1__DOT__counter[0x1aU]) 
                          | vlTOPp->counter1_1__DOT__counter[0x1bU]) 
                         | vlTOPp->counter1_1__DOT__counter[0x1cU]) 
                        | vlTOPp->counter1_1__DOT__counter[0x1dU]) 
                       | vlTOPp->counter1_1__DOT__counter[0x1eU]) 
                      | vlTOPp->counter1_1__DOT__counter[0x1fU]));
    }
    vlTOPp->__Vcellout__counter1_1__o1_out_data = 0U;
    if (vlTOPp->__Vcellinp__counter1_1__o1_out_ready) {
        if ((0U == ((((((((((((((((((((((((((((((((0xaU 
                                                   ^ 
                                                   vlTOPp->counter1_1__DOT__counter[0U]) 
                                                  | vlTOPp->counter1_1__DOT__counter[1U]) 
                                                 | vlTOPp->counter1_1__DOT__counter[2U]) 
                                                | vlTOPp->counter1_1__DOT__counter[3U]) 
                                               | vlTOPp->counter1_1__DOT__counter[4U]) 
                                              | vlTOPp->counter1_1__DOT__counter[5U]) 
                                             | vlTOPp->counter1_1__DOT__counter[6U]) 
                                            | vlTOPp->counter1_1__DOT__counter[7U]) 
                                           | vlTOPp->counter1_1__DOT__counter[8U]) 
                                          | vlTOPp->counter1_1__DOT__counter[9U]) 
                                         | vlTOPp->counter1_1__DOT__counter[0xaU]) 
                                        | vlTOPp->counter1_1__DOT__counter[0xbU]) 
                                       | vlTOPp->counter1_1__DOT__counter[0xcU]) 
                                      | vlTOPp->counter1_1__DOT__counter[0xdU]) 
                                     | vlTOPp->counter1_1__DOT__counter[0xeU]) 
                                    | vlTOPp->counter1_1__DOT__counter[0xfU]) 
                                   | vlTOPp->counter1_1__DOT__counter[0x10U]) 
                                  | vlTOPp->counter1_1__DOT__counter[0x11U]) 
                                 | vlTOPp->counter1_1__DOT__counter[0x12U]) 
                                | vlTOPp->counter1_1__DOT__counter[0x13U]) 
                               | vlTOPp->counter1_1__DOT__counter[0x14U]) 
                              | vlTOPp->counter1_1__DOT__counter[0x15U]) 
                             | vlTOPp->counter1_1__DOT__counter[0x16U]) 
                            | vlTOPp->counter1_1__DOT__counter[0x17U]) 
                           | vlTOPp->counter1_1__DOT__counter[0x18U]) 
                          | vlTOPp->counter1_1__DOT__counter[0x19U]) 
                         | vlTOPp->counter1_1__DOT__counter[0x1aU]) 
                        | vlTOPp->counter1_1__DOT__counter[0x1bU]) 
                       | vlTOPp->counter1_1__DOT__counter[0x1cU]) 
                      | vlTOPp->counter1_1__DOT__counter[0x1dU]) 
                     | vlTOPp->counter1_1__DOT__counter[0x1eU]) 
                    | vlTOPp->counter1_1__DOT__counter[0x1fU]))) {
            vlTOPp->__Vcellout__counter1_1__o1_out_data 
                = (vlTOPp->counter1_1__DOT__counter[0U] 
                   + vlTOPp->__Vcellinp__counter1_1__i1_in_data);
        }
    }
    VL_ASSIGN_SWI(1,vlTOPp->o1_out_valid, vlTOPp->__Vcellout__counter1_1__o1_out_valid);
    VL_ASSIGN_SWI(32,vlTOPp->o1_out_data, vlTOPp->__Vcellout__counter1_1__o1_out_data);
}

void Vcounter1_1::_eval(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_eval\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_combo__TOP__2(vlSymsp);
    if (((IData)(vlTOPp->__Vcellinp__counter1_1__sys_clk) 
         & (~ (IData)(vlTOPp->__Vclklast__TOP____Vcellinp__counter1_1__sys_clk)))) {
        vlTOPp->_sequent__TOP__4(vlSymsp);
    }
    vlTOPp->_combo__TOP__5(vlSymsp);
    // Final
    vlTOPp->__Vclklast__TOP____Vcellinp__counter1_1__sys_clk 
        = vlTOPp->__Vcellinp__counter1_1__sys_clk;
}

void Vcounter1_1::_eval_initial(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_eval_initial\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_initial__TOP__1(vlSymsp);
    vlTOPp->__Vclklast__TOP____Vcellinp__counter1_1__sys_clk 
        = vlTOPp->__Vcellinp__counter1_1__sys_clk;
}

void Vcounter1_1::final() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::final\n"); );
    // Variables
    Vcounter1_1__Syms* __restrict vlSymsp = this->__VlSymsp;
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
}

void Vcounter1_1::_eval_settle(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_eval_settle\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    vlTOPp->_settle__TOP__3(vlSymsp);
}

VL_INLINE_OPT QData Vcounter1_1::_change_request(Vcounter1_1__Syms* __restrict vlSymsp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_change_request\n"); );
    Vcounter1_1* __restrict vlTOPp VL_ATTR_UNUSED = vlSymsp->TOPp;
    // Body
    // Change detection
    QData __req = false;  // Logically a bool
    return __req;
}

#ifdef VL_DEBUG
void Vcounter1_1::_eval_debug_assertions() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_eval_debug_assertions\n"); );
}
#endif  // VL_DEBUG

void Vcounter1_1::_ctor_var_reset() {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcounter1_1::_ctor_var_reset\n"); );
    // Body
    __Vcellinp__counter1_1__sys_rst = VL_RAND_RESET_I(1);
    __Vcellinp__counter1_1__sys_clk = VL_RAND_RESET_I(1);
    __Vcellinp__counter1_1__o1_out_ready = VL_RAND_RESET_I(1);
    __Vcellout__counter1_1__o1_out_valid = VL_RAND_RESET_I(1);
    __Vcellout__counter1_1__o1_out_data = VL_RAND_RESET_I(32);
    __Vcellout__counter1_1__i1_in_ready = VL_RAND_RESET_I(1);
    __Vcellinp__counter1_1__i1_in_data = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(1000, counter1_1__DOT__counter);
    { int __Vi0=0; for (; __Vi0<100; ++__Vi0) {
            counter1_1__DOT__mem1[__Vi0] = VL_RAND_RESET_I(32);
    }}
    { int __Vi0=0; for (; __Vi0<100; ++__Vi0) {
            counter1_1__DOT__mem2[__Vi0] = VL_RAND_RESET_I(32);
    }}
}
