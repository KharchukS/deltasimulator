import glob
from os import path
from tempfile import NamedTemporaryFile
import unittest

import deltalanguage as dl
from deltalanguage.test.execution.test_basic import TestExecutionBasic
from deltalanguage.test._utils import add_non_const

from test._utils import (DUT1,
                         MigenIncrementer,
                         send_gates_list_then_exit)
from test.execution.base import TestExecutionDSBase


ExpT, ExpVal = dl.make_forked_return({'num_out': dl.Int(dl.Size(32)),
                                      'val_out': dl.Bool()})


class TestExecution(TestExecutionDSBase):
    """Some of these tests shall move to Deltalanguage's execution suite.

    The rest are specific to Deltasimulator and will stay here.
    """

    def test_add(self):
        s = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="test_add") as test_graph:
            s.save_and_exit(add_non_const(2, 3))

        self.check_executes_graph(test_graph, "saving 5\n")

    def test_add_64_bit(self):
        @dl.DeltaBlock()
        def return_1() -> dl.Int(dl.Size(64)):
            return 1

        @dl.DeltaBlock()
        def return_2() -> dl.Int(dl.Size(64)):
            return 2

        @dl.DeltaBlock(allow_const=False)
        def add_64_bit(a: dl.Int(dl.Size(64)),
                       b: dl.Int(dl.Size(64))) -> dl.Int(dl.Size(64)):
            return a+b

        s = dl.lib.StateSaver(dl.Int(dl.Size(64)), verbose=True)

        with dl.DeltaGraph(name="test_add_64_bit") as test_graph:
            s.save_and_exit(add_64_bit(a=return_1(), b=return_2()))

        self.check_executes_graph(test_graph, "saving 3\n")

    def test_and(self):
        @dl.DeltaBlock(allow_const=False)
        def bool_and(a: bool, b: bool) -> bool:
            return a and b

        s = dl.lib.StateSaver(bool, verbose=True)

        with dl.DeltaGraph(name="test_and") as test_graph:
            s.save_and_exit(bool_and(a=True, b=False))

        self.check_executes_graph(test_graph, "saving False\n")

    def test_forked(self):
        ForkedReturnT, ForkedReturn = dl.make_forked_return(
            {'a': int, 'b': int})

        @dl.DeltaBlock(allow_const=False)
        def add_2_add_3(n: int) -> ForkedReturnT:
            return ForkedReturn(a=n+2, b=n+3)

        s = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="test_forked") as test_graph:
            ab = add_2_add_3(n=1)
            s.save_and_exit(add_non_const(ab.a, ab.b))

        self.check_executes_graph(test_graph, "saving 7\n")

    def test_interactive_one_in_one_out(self):
        @dl.Interactive([("num", int)],
                        int,
                        name="interactive_one_in_one_out")
        def interactive_func(node: dl.PythonNode):
            for _ in range(2):
                num = node.receive("num")
                print(f"received num: {num}")
            node.send(num + 1)

        s = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="test_interactive_one_in_one_out") as test_graph:
            s.save_and_exit(interactive_func.call(add_non_const(2, 3)))

        self.check_executes_graph(
            test_graph,
            """\
            Interactive_One_In_One_Out_3_module::PyInit_sysc() called 
            received num: 5
            received num: 5
            saving 6
            """)

    def test_interactive_one_in_two_out(self):
        @dl.Interactive([("num", dl.Int(dl.Size(32)))],
                        ExpT,
                        name="interactive_one_in_two_out")
        def interactive_func(node: dl.PythonNode):
            for _ in range(2):
                num = node.receive("num")
                print(f"received num: {num}")
            node.send(ExpVal(num_out=None, val_out=False))
            node.send(ExpVal(num_out=14, val_out=False))

        s0 = dl.lib.StateSaver(bool, condition=lambda x: x)
        s1 = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="interactive_one_in_two_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            s0.save_and_exit_if(int_func.val_out)
            s1.save_and_exit(int_func.num_out)

        self.check_executes_graph(
            test_graph,
            """\
            Interactive_One_In_Two_Out_2_module::PyInit_sysc() called 
            received num: 4
            received num: 4
            saving 14
            """
        )

    def test_interactive_two_in_one_out(self):
        @dl.Interactive([("num", dl.Int(dl.Size(32))),
                         ("opt_val", dl.Optional(dl.Bool()))],
                        dl.Bool(),
                        name="interactive_two_in_one_out")
        def interactive_func(node: dl.PythonNode):
            for _ in range(2):
                num = node.receive("num")
                opt_val = node.receive("opt_val")
                print(f"received opt_val: {opt_val}")
                print(f"received num: {num}")
            node.send(True)

        s = dl.lib.StateSaver(bool, verbose=True, condition=lambda x: x)

        with dl.DeltaGraph(name="interactive_two_in_one_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            s.save_and_exit_if(int_func)

        self.check_executes_graph(
            test_graph,
            """\
            Interactive_Two_In_One_Out_2_module::PyInit_sysc() called 
            received opt_val: True
            received num: 4
            received opt_val: True
            received num: 4
            saving True
            """
        )

    def test_interactive_two_in_two_out(self):
        @dl.Interactive([("num", dl.Int(dl.Size(32))),
                         ("opt_val", dl.Optional(dl.Bool()))],
                        ExpT,
                        name="interactive_two_in_two_out")
        def interactive_func(node: dl.PythonNode):
            for _ in range(2):
                num = node.receive("num")
                opt_val = node.receive("opt_val")
                print(f"received opt_val: {opt_val}")
                print(f"received num: {num}")
            node.send(ExpVal(num_out=None, val_out=False))
            node.send(ExpVal(num_out=14, val_out=False))

        s0 = dl.lib.StateSaver(bool, condition=lambda x: x)
        s1 = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="interactive_two_in_two_out") as test_graph:
            int_func = interactive_func.call(num=4, opt_val=True)
            s0.save_and_exit_if(int_func.val_out)
            s1.save_and_exit(int_func.num_out)

        self.check_executes_graph(
            test_graph,
            """\
            Interactive_Two_In_Two_Out_2_module::PyInit_sysc() called 
            received opt_val: True
            received num: 4
            received opt_val: True
            received num: 4
            saving 14
            """
        )

    def test_splitter(self):
        s = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph(name="test_splitter") as test_graph:
            n = add_non_const(2, 3)
            s.save_and_exit(add_non_const(n, n))

        self.check_executes_graph(test_graph, "saving 10\n")

    def test_migen(self):
        s = dl.lib.StateSaver(int, verbose=True)

        with dl.DeltaGraph("test_migen_wiring") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=1000)
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(i1=c1.o1)
            s.save_and_exit(c2.o1)

        self.check_executes_graph(test_graph, "saving 1020\n")

    def test_migen_template(self):
        s = dl.lib.StateSaver(int, verbose=True)
        empty_node_t = dl.NodeTemplate([('a', int)], int)

        with dl.DeltaGraph("test_migen_template") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=1000)
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(
                i1=empty_node_t.call(a=c1.o1))
            s.save_and_exit(c2.o1)

        self.check_executes_graph(test_graph, "saving 10\n")

    def test_migen_python(self):
        @dl.DeltaBlock(allow_const=False)
        def exit_if_6_else_inc(n: int) -> int:
            print(n)
            if n == 6:
                raise dl.DeltaRuntimeExit
            else:
                return n+1

        with dl.DeltaGraph("test_migen_python") as test_graph:
            ph = dl.placeholder_node_factory()
            c1 = MigenIncrementer(tb_num_iter=2000,
                                  name='counter1',
                                  vcd_name="/workdir/counter1.vcd").call(i1=ph)
            ex = exit_if_6_else_inc(c1.o1)
            ph.specify_by_node(ex)

        self.check_executes_graph(
            test_graph,
            """\
            0
            2
            4
            6
            """
        )

    def test_loop_with_ProjectQ(self):
        with dl.DeltaGraph("test_loop_with_ProjectQ") as test_graph:
            # set up placeholders
            ph_hal_result = dl.placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(
                measurement=ph_hal_result)

            projectQ = dl.lib.HardwareAbstractionLayerNode(
                dl.lib.ProjectqQuantumSimulator(
                    register_size=2,
                    seed=77
                )
            ).accept_command(hal_command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(projectQ)

        self.check_executes_graph(
            test_graph,
            """\
            Interactive_Simple_0_module::PyInit_sysc() called 
            Measurement: 4294901760
            """
        )

    @unittest.skip("Occasionally fails due to a segfault.")
    def test_loop_with_Qiskit(self):
        with dl.DeltaGraph("test_loop_with_Qiskit") as test_graph:
            # set up placeholders
            ph_hal_result = dl.placeholder_node_factory()

            int_func = send_gates_list_then_exit.call(
                measurement=ph_hal_result)

            qiskit = dl.lib.HardwareAbstractionLayerNode(dl.lib.QiskitQuantumSimulator(
                register_size=2, seed=2)).accept_command(command=int_func)
            # tie up placeholders
            ph_hal_result.specify_by_node(qiskit)

        self.check_executes_graph(test_graph)

    def test_state_saver(self):
        store = dl.lib.StateSaver(int)

        with dl.DeltaGraph("test_state_saver") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=1000)
            store.save_and_exit(c1.o1)

        self.check_executes_graph(test_graph)

    def test_state_saver_save_to_file(self):
        with NamedTemporaryFile(mode="w+") as f:
            store = dl.lib.StateSaver(int, filename=f.name)

            with dl.DeltaGraph("test_state_saver_save_to_file") as test_graph:
                store.save_and_exit(1000)

            self.check_executes_graph(test_graph)

            f.seek(0)
            self.assertEqual(f.read(), "1000\n")

    def test_read_file(self):
        filename = path.join("test", "data", "test_add_64_bit.cpp")

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            with open(filename, "r") as txt_file:
                print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph("test_read_file") as test_graph:
            read_txt()

        self.check_executes_graph(test_graph, files=[filename])

    def test_read_multiple_files(self):
        filenames = [path.join("test", "data", "test_add_64_bit.cpp"),
                     path.join("test", "data", "test_add_64_bit.h")]

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            for filename in filenames:
                with open(filename, "r") as txt_file:
                    print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph("test_read_multiple_files") as test_graph:
            read_txt()

        self.check_executes_graph(test_graph, files=filenames)

    def test_read_pattern_files(self):
        pattern = path.join("test", "data", "test_add_*")

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            for filename in glob.glob(pattern):
                with open(filename, "r") as txt_file:
                    print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph("test_read_pattern_files") as test_graph:
            read_txt()

        self.check_executes_graph(test_graph, files=[pattern])

    def test_python_file(self):
        from test.data.code_for_test import x

        @dl.DeltaBlock(allow_const=False)
        def run_code() -> dl.Void:
            print(x)
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph("test_python_file") as test_graph:
            run_code()

        files = [path.join("test", "data", "code_for_test.py"),
                 path.join("test", "__init__.py"),
                 path.join("test", "_utils.py")]

        self.check_executes_graph(test_graph, expect="5\n", files=files)

    def test_package_dependency(self):
        """If a program requires a package that is not installed, use pip
        to import the correct package.

        If we need to rebuild the .df file for some reason repeate
        these steps:
        - Run pip install permutation
        - Run this test with build_df_file set to True
        (This will create a new .df file.)
        - Then run pip uninstall -y permutation
        - Set build_df_file to False
        - Run the actual test, make sure it passes
        """
        df_filename = path.join("test", "data", "permutation.df")

        build_df_file = False
        if build_df_file:
            from permutation import Permutation

            @dl.DeltaBlock(allow_const=False)
            def print_cycles() -> dl.Void:
                print(Permutation(2, 1, 4, 5, 3).to_cycles())
                raise dl.DeltaRuntimeExit

            with dl.DeltaGraph("test_package_dependency") as test_graph:
                print_cycles()

            serialized, _ = dl.serialize_graph(test_graph,
                                               name="dut",
                                               requirements=["permutation"])

            with open(df_filename, "wb") as df_file:
                df_file.write(serialized)

        else:
            self.check_executes_file(df_filename,
                                     expect="[(1, 2), (3, 4, 5)]\n",
                                     reqs=["permutation"])

    def test_incompatible_dependencies(self):
        """If a program requires incompatible dependencies, throw an error.

        If we need to rebuild the .df file for some reason repeate
        these steps:
        - Run pip install permutation
        - Run this test with build_df_file set to True
        (This will create a new .df file.)
        - Then run pip uninstall -y permutation
        - Set build_df_file to False
        - Run the actual test, make sure it passes
        """
        df_filename = path.join("test", "data", "incompatible.df")

        build_df_file = False
        if build_df_file:
            from permutation import Permutation

            @dl.DeltaBlock(allow_const=False)
            def print_cycles() -> dl.Void:
                print(Permutation(2, 1, 4, 5, 3).to_cycles())
                raise dl.DeltaRuntimeExit

            with dl.DeltaGraph("test_incompatible_dependencies") as test_graph:
                print_cycles()

            serialized, _ = dl.serialize_graph(test_graph,
                                               name="dut",
                                               requirements=["permutation<=0.2.0",
                                                             "permutation==0.3.0"])
            with open(df_filename, "wb") as df_file:
                df_file.write(serialized)

        else:
            with self.assertRaises(RuntimeError):
                self.check_executes_file(df_filename,
                                         expect="[(1, 2), (3, 4, 5)]\n")

    @unittest.skip("This test currently fails in a new container.")
    def test_constant_dependency(self):
        """Example where a constant node has a dependency.

        If we need to rebuild the .df file for some reason repeate
        these steps:
        - Run pip install permutation
        - Run this test with build_df_file set to True
        (This will create a new .df file.)
        - Then run pip uninstall -y permutation
        - Set build_df_file to False
        - Run the actual test, make sure it passes

        .. todo::
            Currently this test fails if run in a completely new container.
            This is because pip cannot install to a running program, and
            constant nodes are currently deserialised during the build
            process. This will be fixed in future work.
        """
        df_filename = path.join("test", "data", "constant.df")

        build_df_file = False
        if build_df_file:
            from permutation import Permutation

            @dl.DeltaBlock(allow_const=False)
            def num_cycles() -> dl.Int():
                return len(Permutation(2, 1, 4, 5, 3).to_cycles())

            s = dl.lib.StateSaver(int, verbose=True)

            with dl.DeltaGraph("test_constant_dependency") as test_graph:
                s.save_and_exit(num_cycles())

            serialized, _ = dl.serialize_graph(test_graph,
                                               name="dut",
                                               requirements=["permutation"])

            with open(df_filename, "wb") as df_file:
                df_file.write(serialized)

        else:
            self.check_executes_file(df_filename,
                                     expect="saving 2\n",
                                     reqs=["permutation"])


class TestExecutionNew(TestExecutionDSBase, TestExecutionBasic):
    """Here is an example of how we import tests from Deltalanguage and
    only overwrite execution and testing methods like
    ``check_executes_graph``.

    .. note::
        In multiple inheritance, methods of the first parent are not
        overwritten with methods of the second parent.
    """

    pass


if __name__ == "__main__":
    unittest.main()
