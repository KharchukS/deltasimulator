import migen

from deltalanguage.data_types import (Int,
                                      UInt,
                                      Optional,
                                      Size,
                                      Bool,
                                      Void)
from deltalanguage.runtime import DeltaRuntimeExit
from deltalanguage.wiring import (DeltaBlock,
                                  MigenNodeTemplate,
                                  PythonNode,
                                  Interactive)

from deltalanguage.lib.hal import command_creator


@DeltaBlock()
def add_const(a: int, b: int) -> int:
    return a + b


@DeltaBlock()
def const_exit(a: int) -> Void:
    raise DeltaRuntimeExit


@DeltaBlock(allow_const=False)
def add(a: int, b: int) -> int:
    return a + b


@DeltaBlock(allow_const=False)
def print_then_exit(n: int) -> Void:
    print(n)
    raise DeltaRuntimeExit


@DeltaBlock(allow_const=False)
def print_then_exit_64_bit(n: Int(Size(64))) -> Void:
    print(n)
    raise DeltaRuntimeExit


@DeltaBlock(allow_const=False)
def exit_if_true(cond: bool) -> Void:
    if cond:
        raise DeltaRuntimeExit


@DeltaBlock()
def return_1000() -> Int(Size(32)):
    return 1000


class DUT1(MigenNodeTemplate):

    def migen_body(self, template):
        # I/O:
        i1 = template.add_pa_in_port("i1", Optional(int))
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


class MigenIncrementer(MigenNodeTemplate):

    def migen_body(self, template):
        # I/O:
        i1 = template.add_pa_in_port("i1", Optional(int))
        o1 = template.add_pa_out_port("o1", int)

        self.comb += (
            i1.ready.eq(1),
        )

        started = migen.Signal(1)

        self.sync += migen.If(
            i1.valid == 1,
            o1.valid.eq(1),
            o1.data.eq(i1.data+1)
        ).Else(
            o1.data.eq(0),
            migen.If(started == 0,
                     o1.valid.eq(1),
                     started.eq(1)
                     ).Else(
                o1.valid.eq(0)
            )
        )


@Interactive([("measurement", UInt(Size(32)))],
             UInt(Size(32)),
             name="interactive_simple")
def send_gates_list_then_exit(node: PythonNode):
    cmds = ["RX", "RZ", "RY"]
    # for non-dererministic tests use random.randint(0, 255)
    args = [99, 250, 11]

    node.send(command_creator("STATE_PREPARATION"))

    for cmd, arg in zip(cmds, args):
        node.send(command_creator(cmd, argument=arg))
    node.send(command_creator("STATE_MEASURE"))

    measurement = node.receive("measurement")
    print(f"Measurement: {measurement}")

    raise DeltaRuntimeExit
