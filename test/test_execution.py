import unittest
import subprocess
from os import path, chmod, environ
import shutil
from tempfile import TemporaryDirectory

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
from deltalanguage.lib import StateSaver
from deltasimulator.lib import build_graph

from test._utils import (DUT1,
                         MigenIncrementer,
                         add,
                         print_then_exit,
                         print_then_exit_64_bit,
                         exit_if_true,
                         return_1000,
                         send_gates_list_then_exit)


ExpT, ExpVal = make_forked_return({'num_out': DInt(DSize(32)), 'val_out': DBool()})

class TestExecution(unittest.TestCase):

    def check_executes(self, graph, expect: str=None, files=[]):
        """Build SystemC program and executes them in temp directory."""
        _, program = serialize_graph(graph, name="dut", files=files)
        self.files = files
        for file in files:
            shutil.move(file, f"{file}_temp")
        shutil.rmtree("__pycache__", ignore_errors=True)
        with TemporaryDirectory() as build_dir:
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
            if expect:
                self.assertRegex(_proc.stdout.decode(), expect,
                    f"{_proc.stdout.decode()} does not match with the provided regex")


    def test_add(self):
        with DeltaGraph(name="test_add") as test_graph:
            print_then_exit(n=add(a=2, b=3))

        self.check_executes(test_graph, "5")

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

        self.check_executes(test_graph, "3")

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

        self.check_executes(test_graph, "False")

    def test_forked(self):
        ForkedReturnT, ForkedReturn = make_forked_return({'a': int, 'b': int})

        @DeltaBlock(allow_const=False)
        def add_2_add_3(n: int) -> ForkedReturnT:
            return ForkedReturn(a=n+2, b=n+3)

        with DeltaGraph(name="test_forked") as test_graph:
            ab = add_2_add_3(n=1)
            print_then_exit(n=add(a=ab.a, b=ab.b))

        self.check_executes(test_graph, "7")

    def test_interactive_one_in_one_out(self):
        @Interactive(in_params={"num": int}, out_type=int, name="interactive_one_in_one_out")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(2):
                num = node.receive("num")
                print(f"received num: {num}")
            node.send(num + 1)

        with DeltaGraph(name="test_interactive_one_in_one_out") as test_graph:
            print_then_exit(n=interactive_func.call(num=add(a=2, b=3)))

        self.check_executes(test_graph, "received num: 5\\nreceived num: 5\\n6")

    def test_interactive_one_in_two_out(self):
        @Interactive(in_params={"num": DInt(DSize(32))}, out_type=ExpT, name="interactive_one_in_two_out")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(2):
                num = node.receive("num")
                print(f"received num: {num}")
            node.send(ExpVal(num_out=None, val_out=False))
            node.send(ExpVal(num_out=14, val_out=False))

        with DeltaGraph(name="interactive_one_in_two_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            exit_if_true(cond=int_func.val_out)
            print_then_exit(n=int_func.num_out)
        self.check_executes(test_graph, "received num: 4\\nreceived num: 4\\n14")


    def test_interactive_two_in_one_out(self):
        @Interactive(in_params={"num": DInt(DSize(32)), "opt_val": DOptional(DBool())}, out_type=DBool(), name="interactive_two_in_one_out")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(2):
                num = node.receive("num")
                opt_val = node.receive("opt_val")
                print(f"received opt_val: {opt_val}")
                print(f"received num: {num}")
            node.send(True)

        with DeltaGraph(name="interactive_two_in_one_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            exit_if_true(cond=int_func)
        self.check_executes(test_graph, "received opt_val: True\\nreceived num: 4\\nreceived opt_val: True\\nreceived num: 4")

    def test_interactive_two_in_two_out(self):
        @Interactive(in_params={"num": DInt(DSize(32)), "opt_val": DOptional(DBool())}, out_type=ExpT, name="interactive_two_in_two_out")
        def interactive_func(node: PyInteractiveNode):
            for _ in range(2):
                num = node.receive("num")
                opt_val = node.receive("opt_val")
                print(f"received opt_val: {opt_val}")
                print(f"received num: {num}")
            node.send(ExpVal(num_out=None, val_out=False))
            node.send(ExpVal(num_out=14, val_out=False))

        with DeltaGraph(name="interactive_two_in_two_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            exit_if_true(cond=int_func.val_out)
            print_then_exit(n=int_func.num_out)
        self.check_executes(test_graph, "received opt_val: True\\nreceived num: 4\\nreceived opt_val: True\\nreceived num: 4\\n14")



    def test_splitter(self):
        with DeltaGraph(name="test_splitter") as test_graph:
            n = add(a=2, b=3)
            print_then_exit(n=add(a=n, b=n))

        self.check_executes(test_graph, "10")


    def test_migen(self):
        with DeltaGraph("test_migen_wiring") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(i1=c1.o1)
            print_then_exit(c2.o1)

        self.check_executes(test_graph, "10")

    def test_migen_template(self):
        with DeltaGraph("test_migen_template") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(
                i1=template_node_factory(return_type=int, a=c1.o1))
            print_then_exit(c2.o1)

        self.check_executes(test_graph, "10")

    def test_migen_python(self):
        @DeltaBlock(allow_const=False)
        def exit_if_6_else_inc(n: int) -> int:
            print (n)
            if n == 6:
                raise DeltaRuntimeExit
            else :
                return n+1

        with DeltaGraph("test_migen_python") as test_graph:
            ph = placeholder_node_factory()
            c1 = MigenIncrementer(tb_num_iter=2000, name='counter1', vcd_name="/workdir/counter1.vcd").call(i1=ph)
            ex = exit_if_6_else_inc(c1.o1)
            ph.specify_by_node(ex)
        self.check_executes(test_graph, "0\\n2\\n4\\n6\\n")


    def test_loop_with_ProjectQ(self):
        with DeltaGraph("test_loop_with_ProjectQ") as test_graph:
            # set up placeholders
            ph_hal_result = placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(measurement=ph_hal_result)

            projectQ = HardwareAbstractionLayerNode(ProjectqQuantumSimulator(register_size=2)).accept_command(command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(projectQ)

        self.check_executes(test_graph, "Measurement: 429490176[0-1]")

    def test_loop_with_Qiskit(self):
        with DeltaGraph("test_loop_with_Qiskit") as test_graph:
            # set up placeholders
            ph_hal_result = placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(measurement=ph_hal_result)

            qiskit = HardwareAbstractionLayerNode(QiskitQuantumSimulator(register_size=2, seed=2)).accept_command(command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(qiskit)

        self.check_executes(test_graph)

    def test_state_saver(self):
        store = StateSaver(int)
        with DeltaGraph("test_state_saver") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            store.save_and_exit(c1.o1)
        self.check_executes(test_graph)

    def test_read_file(self):
        @DeltaBlock(allow_const=False)
        def read_txt() -> NoMessage:
            with open(".gitignore", "r") as txt_file:
                print(txt_file.read())
            raise DeltaRuntimeExit
        with DeltaGraph("test_read_file") as test_graph:
            read_txt()
        self.check_executes(test_graph, files=[".gitignore"])

    def test_read_multiple_files(self):
        @DeltaBlock(allow_const=False)
        def read_txt() -> NoMessage:
            with open(".gitignore", "r") as txt_file:
                print(txt_file.read())
            with open("CODE_OF_CONDUCT.md", "r") as txt_file:
                print(txt_file.read())
            raise DeltaRuntimeExit
        with DeltaGraph("test_read_file") as test_graph:
            read_txt()
        self.check_executes(test_graph, files=[".gitignore", "CODE_OF_CONDUCT.md"])

    def test_python_file(self):
        import code_for_test
        @DeltaBlock(allow_const=False)
        def run_code() -> NoMessage:
            print(code_for_test.x)
            raise DeltaRuntimeExit
        with DeltaGraph("test_python_file") as test_graph:
            run_code()
        self.check_executes(test_graph, expect="5", files=["code_for_test.py"])


    def tearDown(self):
        DeltaGraph.clean_stack()
        for file in self.files:
            shutil.move(f"{file}_temp", file)


if __name__ == "__main__":
    unittest.main()
