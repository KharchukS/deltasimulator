import unittest
import subprocess
from os import path, chmod, environ

from deltalanguage.data_types import DInt, DSize, NoMessage, make_forked_return, DOptional, DBool
from deltalanguage.wiring import (DeltaBlock,
                                  DeltaGraph,
                                  template_node_factory,
                                  Interactive,
                                  PyInteractiveNode,
                                  placeholder_node_factory)
from deltalanguage.runtime import DeltaRuntimeExit, serialize_graph
from deltalanguage.lib.quantum_simulators import QiskitQuantumSimulator, ProjectqQuantumSimulator
from deltalanguage.lib.hal import command_creator, HardwareAbstractionLayerNode

from deltasimulator.lib import build_graph

from test._utils import (DUT1,
                         add,
                         print_then_exit,
                         print_then_exit_64_bit,
                         exit_if_true,
                         return_1000,
                         send_gates_list_then_exit)
import tempfile

ExpT, ExpVal = make_forked_return({'num_out': DInt(DSize(32)), 'val_out': DBool()})

class TestExecution(unittest.TestCase):

    def check_executes(self, graph):
        """Build SystemC program and executes them in temp directory."""
        _, program = serialize_graph(graph, name="dut")
        with tempfile.TemporaryDirectory() as build_dir:
            build_graph(program, main_cpp=path.join(path.dirname(__file__), "main.cpp"),
            build_dir=build_dir)
            # Setting the permission to run the file
            chmod(f"{build_dir}/main", 0o777)
            try:
                # We disable the SYSTEMC Banner to clear the output by setting the
                # SYSTEMC_DISABLE_COPYRIGHT_MESSAGE
                _proc = subprocess.run("./main", cwd=build_dir, shell=True,
                    check=True, stdout = subprocess.PIPE, env=dict(environ,
                    SYSTEMC_DISABLE_COPYRIGHT_MESSAGE="1"))
            except subprocess.CalledProcessError as e:
                print(f"Failure in running: {e.returncode} - {e.output}")
                raise e

    def test_add(self):
        with DeltaGraph(name="test_add") as test_graph:
            print_then_exit(n=add(a=2, b=3))

        self.check_executes(test_graph)

    def test_add_64_bit(self):
        @DeltaBlock()
        def return_1() -> DInt(DSize(64)):
            return 1

        @DeltaBlock()
        def return_2() -> DInt(DSize(64)):
            return 2

        @DeltaBlock(allow_const=False)
        def add_64_bit(a: DInt(DSize(64)), b: DInt(DSize(64))) -> DInt(DSize(64)):
            return a+b

        with DeltaGraph(name="test_add_64_bit") as test_graph:
            print_then_exit_64_bit(n=add_64_bit(a=return_1(), b=return_2()))

        self.check_executes(test_graph)

    def test_and(self):
        @DeltaBlock(allow_const=False)
        def bool_and(a: bool, b: bool) -> bool:
            return a and b

        @DeltaBlock(allow_const=False)
        def print_then_exit_bool(x: bool) -> NoMessage:
            print(x)
            raise DeltaRuntimeExit

        with DeltaGraph(name="test_and") as test_graph:
            print_then_exit_bool(x=bool_and(a=True, b=False))

        self.check_executes(test_graph)

    def test_forked(self):
        ForkedReturnT, ForkedReturn = make_forked_return({'a': int, 'b': int})

        @DeltaBlock(allow_const=False)
        def add_2_add_3(n: int) -> ForkedReturnT:
            return ForkedReturn(a=n+2, b=n+3)

        with DeltaGraph(name="test_forked") as test_graph:
            ab = add_2_add_3(n=1)
            print_then_exit(n=add(a=ab.a, b=ab.b))

        self.check_executes(test_graph)

    def test_interactive_simple(self):
        @Interactive(in_params={"num": int}, out_type=int, name="interactive_simple")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(10):
                num = node.receive("num")
                print(f"received num: {num}")
            node.send(num + 1)

        with DeltaGraph(name="test_interactive_simple") as test_graph:
            print_then_exit(n=interactive_func.call(num=add(a=2, b=3)))

        self.check_executes(test_graph)

    def test_interactive_complex(self):
        @Interactive(in_params={"num": DInt(DSize(32)), "opt_val": DOptional(DInt(DSize(32)))}, out_type=ExpT, name="interactive_complex")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(10):
                num = node.receive("num")
                opt_val = node.receive("opt_val")
                print(f"received opt_val: {opt_val}")
                print(f"received num: {num}")
            node.send(ExpVal(num_out=num, val_out=False))

        with DeltaGraph(name="interactive_complex") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=5)
            exit_if_true(cond=int_func.val_out)
            print_then_exit(n=int_func.num_out)
        self.check_executes(test_graph)


    def test_splitter(self):
        with DeltaGraph(name="test_splitter") as test_graph:
            n = add(a=2, b=3)
            print_then_exit(n=add(a=n, b=n))

        self.check_executes(test_graph)

    def test_migen(self):
        with DeltaGraph("test_migen_wiring") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(i1=c1.o1)
            print_then_exit(c2.o1)

        self.check_executes(test_graph)

    def test_migen_template(self):
        with DeltaGraph("test_migen_template") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(
                i1=template_node_factory(return_type=int, a=c1.o1))
            print_then_exit(c2.o1)

        self.check_executes(test_graph)

    def test_loop_with_ProjectQ(self):
        with DeltaGraph("test_loop_with_ProjectQ") as test_graph:
            # set up placeholders
            ph_hal_result = placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(measurement=ph_hal_result)

            projectQ = HardwareAbstractionLayerNode(ProjectqQuantumSimulator(register_size=2)).accept_command(command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(projectQ)

        self.check_executes(test_graph)

    @unittest.skip("This test still requires investigations on teardown")
    def test_loop_with_Qiskit(self):
        with DeltaGraph("test_loop_with_Qiskit") as test_graph:
            # set up placeholders
            ph_hal_result = placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(measurement=ph_hal_result)

            qiskit = HardwareAbstractionLayerNode(QiskitQuantumSimulator(register_size=2, seed=2)).accept_command(command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(qiskit)

        self.check_executes(test_graph)


    def tearDown(self):
        DeltaGraph.clean_stack()


if __name__ == "__main__":
    unittest.main()
