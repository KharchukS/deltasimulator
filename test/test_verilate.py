import asyncio
import unittest
from os import path

import dill

from deltalanguage.data_types import DFloat, DInt, DUInt
from deltalanguage.runtime import serialize_graph
from deltalanguage.wiring import DeltaGraph
from deltasimulator.build_tools import BuildArtifact
from deltasimulator.build_tools.environments import VerilatorEnv

from test._utils import DUT1, print_then_exit, return_1000

class TestVerilator(unittest.TestCase):

    def test_float_width_sum(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(DFloat())), "sc_bv<32>")

    def test_int_size(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(DInt())), "sc_bv<32>")

    def test_unit_size(self):
        with VerilatorEnv() as env:
            self.assertEqual(env.as_c_type(dill.dumps(DUInt())), "sc_bv<32>")

    def test_migen_node(self):
        with DeltaGraph() as test_graph:
            c1 = DUT1(tb_num_iter=2000, name='counter1').call(i1=return_1000())
            print_then_exit(c1.o1)
        _, serialised = serialize_graph(test_graph)
        top_v = BuildArtifact(name=f"{serialised.nodes[1].name}",
                              data=serialised.bodies[1].migen.verilog.encode("utf-8"))
        with VerilatorEnv() as env:
            build_artifacts = env.verilate(top_v)
        asyncio.run(self.assert_build_correct(build_artifacts))

    async def assert_build_correct(self, build_artifacts):
        """Build artifacts and check the compiled code is correct."""
        built = {}
        built["cpp"] = await asyncio.wait_for(build_artifacts["cpp"].data,
                                              timeout=None)
        built["h"] = await asyncio.wait_for(build_artifacts["h"].data,
                                            timeout=None)
        built["ALL.a"] = await asyncio.wait_for(build_artifacts["ALL.a"].data,
                                                timeout=None)
        built["verilated.o"] = await asyncio.wait_for(
            build_artifacts["verilated.o"].data, timeout=None)
        built["init1"] = await asyncio.wait_for(build_artifacts["init"][0].data,
                                               timeout=None)
        built["init2"] = await asyncio.wait_for(build_artifacts["init"][1].data,
                                               timeout=None)
        with open(path.join("test", "data", "verilated_cpp.out"), "rb") as cpp_file:
            self.assertEqual(cpp_file.read(), built["cpp"])
        with open(path.join("test", "data", "verilated_h.out"), "rb") as h_file:
            self.assertEqual(h_file.read(), built["h"])
        with open(path.join("test", "data", "verilated_init1.out"), "rb") as init_file:
            self.assertEqual(init_file.read(), built["init1"])
        with open(path.join("test", "data", "verilated_init2.out"), "rb") as init_file:
            self.assertEqual(init_file.read(), built["init2"])

    def tearDown(self):
        DeltaGraph.clean_stack()


if __name__ == "__main__":
    unittest.main()
