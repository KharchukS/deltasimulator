import asyncio
import unittest
from os import path

import dill

from deltalanguage.data_types import Float, Int, UInt
from deltalanguage.runtime import serialize_graph
from deltalanguage.wiring import DeltaGraph
from deltalanguage.test._node_lib import DUT1

from deltasimulator.build_tools import BuildArtifact
from deltasimulator.build_tools.environments import VerilatorEnv

from test._utils import print_then_exit, return_1000


class TestVerilator(unittest.TestCase):

    def setUp(self):
        DeltaGraph.clean_stack()
        self.maxDiff = None

    def test_float_width_sum(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(Float())), "sc_bv<32>")

    def test_int_size(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(Int())), "sc_bv<32>")

    def test_unit_size(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(UInt())), "sc_bv<32>")

    def test_migen_node(self):
        with DeltaGraph() as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            print_then_exit(c1.o1)

        _, serialised = serialize_graph(test_graph)

        top_v = BuildArtifact(
            name=f"{serialised.nodes[1].name}",
            data=serialised.bodies[1].migen.verilog.encode("utf-8")
        )

        with VerilatorEnv() as env:
            build_artifacts = env.verilate(top_v)

        asyncio.run(self.assert_build_correct(build_artifacts))

    async def assert_build_correct(self, build_artifacts):
        """Build artifacts and check the compiled code is correct."""
        built = {}
        built["cpp"] = await asyncio.wait_for(
            build_artifacts["cpp"].data,
            timeout=None
        )
        built["h"] = await asyncio.wait_for(
            build_artifacts["h"].data,
            timeout=None
        )
        built["ALL.a"] = await asyncio.wait_for(
            build_artifacts["ALL.a"].data,
            timeout=None
        )
        built["verilated.o"] = await asyncio.wait_for(
            build_artifacts["verilated.o"].data,
            timeout=None
        )
        built["init1"] = await asyncio.wait_for(
            build_artifacts["init"][0].data,
            timeout=None
        )
        built["init2"] = await asyncio.wait_for(
            build_artifacts["init"][1].data,
            timeout=None
        )

        with open(path.join("test", "data", "verilated.cpp"), "rb") as f:
            ref = f.read().decode("utf-8")
            gen = built["cpp"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref)

        with open(path.join("test", "data", "verilated.h"), "rb") as f:
            ref = f.read().decode("utf-8")
            gen = built["h"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref)

        with open(path.join("test", "data", "verilated1.init"), "rb") as f:
            ref = f.read().decode("utf-8")
            gen = built["init1"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref)

        with open(path.join("test", "data", "verilated2.init"), "rb") as f:
            ref = f.read().decode("utf-8")
            gen = built["init2"].decode("utf-8")
            self.assertMultiLineEqual(gen, ref)


if __name__ == "__main__":
    unittest.main()
