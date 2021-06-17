import asyncio
import unittest
from os import path

from deltalanguage.data_types import Int, Size, Void
from deltalanguage.wiring import (DeltaBlock,
                                  DeltaGraph,
                                  NodeTemplate,
                                  Interactive,
                                  PythonNode)
from deltalanguage.runtime import DeltaRuntimeExit, serialize_graph
from deltalanguage.test._node_lib import DUT1

from deltasimulator.lib import generate_wiring, _wait_for_build

from test._utils import (add,
                         add_const,
                         print_then_exit,
                         print_then_exit_64_bit,
                         return_1000)


class TestWiring(unittest.TestCase):

    def setUp(self):
        DeltaGraph.clean_stack()
        self.maxDiff = None

    def check_build(self, test_graph):
        """Build SystemC program and run tests."""
        _, program = serialize_graph(test_graph)
        _, _, wiring = generate_wiring(program)
        asyncio.run(self.assert_build_correct(wiring, test_graph.name))

    async def assert_build_correct(self, wiring, prog_name):
        """Build artifacts and check the compiled code is correct.
        Artifacts related to ``sc_main`` will not exist if there are
        template nodes.
        """
        built = {}
        if f"{prog_name}.cpp" in wiring:
            built[f"{prog_name}.cpp"] = await asyncio.wait_for(
                wiring[f"{prog_name}.cpp"].data,
                timeout=None
            )

            with open(path.join("test", "data", f"{prog_name}.cpp"),
                      "rb") as cpp_file:
                ref = cpp_file.read().decode("utf-8")
                gen = built[f"{prog_name}.cpp"].decode("utf-8")
                self.assertMultiLineEqual(gen, ref)

        built[f"{prog_name}.a"] = await asyncio.wait_for(
            wiring[f"{prog_name}.a"].data,
            timeout=None
        )

        built[f"{prog_name}.h"] = await asyncio.wait_for(
            wiring[f"{prog_name}.h"].data,
            timeout=None
        )

        with open(path.join("test", "data", f"{prog_name}.h"),
                  "rb") as h_file:
            ref = h_file.read().decode("utf-8")
            gen = built[f"{prog_name}.h"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref)

        if f"{prog_name}.o" in wiring:
            built[f"{prog_name}.o"] = await asyncio.wait_for(
                wiring[f"{prog_name}.o"].data,
                timeout=None
            )
        if f"{prog_name}" in wiring:
            built[f"{prog_name}"] = await asyncio.wait_for(
                wiring[f"{prog_name}"].data,
                timeout=None
            )

    def test_add(self):
        with DeltaGraph(name="test_add") as test_graph:
            print_then_exit(n=add(a=2, b=3))

        self.check_build(test_graph)

    def test_add_64_bit(self):
        @DeltaBlock()
        def return_1() -> Int(Size(64)):
            return 1

        @DeltaBlock()
        def return_2() -> Int(Size(64)):
            return 2

        @DeltaBlock(allow_const=False)
        def add_64_bit(a: Int(Size(64)),
                       b: Int(Size(64))) -> Int(Size(64)):
            return a + b

        with DeltaGraph(name="test_add_64_bit") as test_graph:
            print_then_exit_64_bit(n=add_64_bit(a=return_1(), b=return_2()))

        self.check_build(test_graph)

    def test_and(self):
        @DeltaBlock(allow_const=False)
        def bool_and(a: bool, b: bool) -> bool:
            return a and b

        @DeltaBlock(allow_const=False)
        def print_then_exit_bool(x: bool) -> Void:
            print(x)
            raise DeltaRuntimeExit

        with DeltaGraph(name="test_and") as test_graph:
            print_then_exit_bool(x=bool_and(a=True, b=False))

        self.check_build(test_graph)

    def test_forked(self):
        @DeltaBlock(outputs=[('a', int), ('b', int)], allow_const=False)
        def add_2_add_3(n: int):
            return n+2, n+3

        with DeltaGraph(name="test_forked") as test_graph:
            ab = add_2_add_3(n=1)
            print_then_exit(n=add(a=ab.a, b=ab.b))

        self.check_build(test_graph)

    def test_interactive(self):
        @Interactive([("num", int)], [("output", int)], name="interactive")
        def interactive_func(node: PythonNode):
            for _ in range(10):
                num = node.receive()["num"]
                print(f"received num: {num}")
            node.send(num + 1)

        with DeltaGraph(name="test_interactive") as test_graph:
            print_then_exit(n=interactive_func.call(num=add(a=2, b=3)))

        self.check_build(test_graph)

    def test_splitter(self):
        with DeltaGraph(name="test_splitter") as test_graph:
            n = add(a=2, b=3)
            print_then_exit(n=add(a=n, b=n))

        self.check_build(test_graph)

    def test_migen(self):
        with DeltaGraph("test_migen_wiring") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(i1=c1.o1)
            print_then_exit(c2.o1)

        self.check_build(test_graph)

    def test_python_template(self):
        py_template = NodeTemplate([('a', int), ('b', int)], [('out', int)])

        with DeltaGraph("test_python_template") as test_graph:
            print_then_exit(py_template.call(a=1, b=2))

        self.check_build(test_graph)

    def test_migen_template(self):
        migen_template = NodeTemplate([('a', int)], [('out', int)])

        with DeltaGraph("test_migen_template") as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            c2 = DUT1(tb_num_iter=2000, name='counter2').call(
                i1=migen_template.call(a=c1.o1))
            print_then_exit(c2.o1)

        self.check_build(test_graph)

    def test_const_graph(self):
        with DeltaGraph("test_const_graph") as test_graph:
            add_const(a=5, b=6)

        with self.assertRaises(RuntimeError):
            self.check_build(test_graph)


if __name__ == "__main__":
    unittest.main()
