import migen

from deltalanguage.data_types import Int, Size, Void
from deltalanguage.runtime import DeltaRuntimeExit
from deltalanguage.wiring import DeltaBlock


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
