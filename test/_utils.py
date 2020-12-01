import migen

from deltalanguage.data_types import (DInt,
                                      DOptional,
                                      DSize,
                                      NoMessage, 
                                      DBool)
from deltalanguage.runtime import DeltaRuntimeExit
from deltalanguage.wiring import DeltaBlock, MigenNodeTemplate

from os import makedirs

@DeltaBlock()
def add_const(a: int, b: int) -> int:
    return a + b


@DeltaBlock()
def const_exit(a: int) -> NoMessage:
    raise DeltaRuntimeExit


@DeltaBlock(allow_const=False)
def add(a: int, b: int) -> int:
    return a + b


@DeltaBlock(allow_const=False)
def print_then_exit(n: int) -> NoMessage:
    print(n)
    raise DeltaRuntimeExit


@DeltaBlock(allow_const=False)
def print_then_exit_64_bit(n: DInt(DSize(64))) -> NoMessage:
    print(n)
    raise DeltaRuntimeExit

@DeltaBlock(allow_const=False)
def exit_if_true(cond: bool) -> NoMessage:
    if cond:
        raise DeltaRuntimeExit

@DeltaBlock()
def return_1000() -> DInt(DSize(32)):
    return 1000


class DUT1(MigenNodeTemplate):

    def migen_body(self, template):
        # I/O:
        i1 = template.add_pa_in_port("i1", DOptional(int))
        o1 = template.add_pa_out_port("o1", int)

        # LOGIC:
        self.counter = migen.Signal(1000)
        self.sync += self.counter.eq(self.counter + 1)

        # Two memories for testing
        self.specials.mem1 = mem1 = migen.Memory(32, 100, init=[5, 15, 32])
        read_port1 = mem1.get_port()
        self.specials.mem2 = mem2 = migen.Memory(32, 100, init=[2, 4, 6, 8])
        read_port2 = mem2.get_port()
        self.specials += read_port1
        self.specials += read_port2
        self.mem_out1 = migen.Signal(32)
        self.mem_out2 = migen.Signal(32)

        self.sync += (read_port1.adr.eq(self.counter),
            self.mem_out1.eq(read_port1.dat_r))

        self.sync += (read_port2.adr.eq(self.counter),
            self.mem_out2.eq(read_port2.dat_r))

        # DEBUGGING:
        # add any signal you want to see in debugging and printing format
        # (in_ports, out_ports, inputs, output are added by default):
        self.debug_signals = {'counter': (self.counter, '05b')}

        self.comb += migen.If(
            self.counter >= 5,
            i1.ready.eq(1)
        )

        self.comb += migen.If(
            o1.ready == 1,
            migen.If(
                self.counter == 10,
                o1.data.eq(self.counter+i1.data),
                o1.valid.eq(1)
            ).Else(
                o1.valid.eq(0)
            )
        )



