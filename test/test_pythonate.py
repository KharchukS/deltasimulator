import asyncio
import unittest
from os import path
import re

from deltalanguage.data_types import DOptional
from deltalanguage.wiring import DeltaGraph, Interactive, PyInteractiveNode
from deltalanguage.runtime import serialize_graph
from deltasimulator.build_tools.environments import PythonatorEnv

from test._utils import add, const_exit, print_then_exit

@Interactive(in_params={"num": int, "val": int, "opt": DOptional(int)}, out_type=int, name="pythonate_interactive")
def interactive_func(node: PyInteractiveNode):
    while(True):
        num = node.receive()["num"]
        print (f"received num = {num}")
        opt = node.receive()["opt"]
        if opt:
            print (f"received opt={opt}")
        val = node.receive()["val"]
        node.send(num + val + 1)

class TestPythonator(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPythonator, self).__init__(*args, **kwargs)
        self.build_artifacts = None

    async def assert_build_correct(self, prefix):
        print (f"checking {prefix} artifacts")
        built = {}
        built["cpp"] = await asyncio.wait_for(self.build_artifacts["cpp"].data,
                                              timeout=None)
        built["h"] = await asyncio.wait_for(self.build_artifacts["h"].data,
                                            timeout=None)
        if "py" in self.build_artifacts:
            built["py"] = await asyncio.wait_for(self.build_artifacts["py"].data,
                                                 timeout=None)
        built["o"] = await asyncio.wait_for(self.build_artifacts["o"].data,
                                            timeout=None)
        maxDiff = self.maxDiff
        self.maxDiff = None
        with open(path.join("test", "data", "pythonate", f"{prefix}_pythonate_cpp.out"), "rb") as cpp_file:
            gen = built["cpp"].decode("utf-8")
            ref = cpp_file.read().decode("utf-8")
            self.assertMultiLineEqual(gen, ref, f"{prefix}_pythonate_cpp.out does not match built file")
        with open(path.join("test", "data", "pythonate", f"{prefix}_pythonate_h.out"), "rb") as h_file:
            ref = h_file.read().decode("utf-8")
            gen = built["h"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref, f"{prefix}_pythonate_h.out does not match built file")
        with open(path.join("test", "data", "pythonate", f"{prefix}_pythonate_py.out"), "rb") as py_file:
            # Remove pickled portion - we can't guarantee the same result with unittest vs normal generation
            ref = py_file.read().decode("utf-8")
            gen = built["py"].decode("utf-8")
            filt = r"loads\(.*\)"
            self.assertMultiLineEqual(re.sub(filt,'loads(...)',gen, flags=re.MULTILINE),
                                      re.sub(filt,'loads(...)',ref, flags=re.MULTILINE),
                                      f"{prefix}_pythonate_py.out does not match built file")
        self.maxDiff = maxDiff

    def test_pythonate(self):
        """Build artifacts and check the compiled code is correct."""
        with DeltaGraph() as test_graph:
            print_then_exit(n=interactive_func.call(num=add(a=2, b=3), val=4, opt=4))

        _, program = serialize_graph(test_graph)
        for node in program.nodes:
            if "add" in node.name:
                with PythonatorEnv(program.bodies) as env:
                    self.build_artifacts = env.pythonate(node)
                asyncio.run(self.assert_build_correct("add"))
            elif "interactive" in node.name:
                with PythonatorEnv(program.bodies) as env:
                    self.build_artifacts = env.pythonate(node)
                asyncio.run(self.assert_build_correct("interactive"))

    def test_const_exit(self):
        with DeltaGraph() as test_graph:
            const_exit(a=5)

        _, program = serialize_graph(test_graph)
        with PythonatorEnv(program.bodies) as env:
            self.build_artifacts = env.pythonate(program.nodes[1])
        with self.assertRaises(ValueError):
            asyncio.run(self.build_artifacts["cpp"].data)

    def tearDown(self):
        DeltaGraph.clean_stack()


if __name__ == "__main__":
    unittest.main()
