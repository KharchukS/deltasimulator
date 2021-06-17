import asyncio
from copy import deepcopy
import subprocess
import unittest

from deltalanguage.data_types import Int, Optional, Void
from deltalanguage.wiring import DeltaBlock, DeltaGraph, NodeTemplate
from deltalanguage.runtime import DeltaRuntimeExit, serialize_graph

from deltasimulator.lib import generate_wiring


class TestBodySelection(unittest.TestCase):

    async def assert_tag_from_py_script(self, build_artifact, tag):
        built = await asyncio.wait_for(
            build_artifact.data,
            timeout=None
        )

        python_string = built.decode("utf-8") + "\nprint(body.access_tags[0])"

        p = subprocess.run(
            [r"python"],
            input=str.encode(python_string),
            stdout=subprocess.PIPE,
            check=False
        )
        output = p.stdout.decode()
        self.assertEqual(output, tag + "\n")

    def setUp(self):

        self.test_template = NodeTemplate(
            name="TestTemplate",
            inputs=[('a', int), ('b', int)]
        )

        @DeltaBlock(
            template=self.test_template,
            allow_const=False,
            tags=["func_1"]
        )
        def func_1(a: int, b: int) -> Void:
            print("func_1")
            raise DeltaRuntimeExit

        @DeltaBlock(
            template=self.test_template,
            allow_const=False,
            tags=["func_2", "preferred"]
        )
        def func_2(a: int, b: int) -> Void:
            print("func_2")
            raise DeltaRuntimeExit

        @DeltaBlock(
            template=self.test_template,
            allow_const=False,
            tags=["func_3", "excluded"]
        )
        def func_3(a: int, b: int) -> Void:
            print("func_3")
            raise DeltaRuntimeExit

    def test_select_preferred_node_body(self):

        with DeltaGraph() as graph:
            n = self.test_template.call(1, 2)

        # start on a body different form the desired
        n.select_body(preferred=["func_1"])

        _, self.program = serialize_graph(graph)

        node_bodies, _, _ = generate_wiring(
            self.program,
            preferred_body_tags=["preferred"]
        )

        self.assertEqual(len(node_bodies), 1)
        asyncio.run(self.assert_tag_from_py_script(node_bodies[0], "func_2"))

    def test_no_select_excluded_node_body(self):

        with DeltaGraph() as graph:
            n = self.test_template.call(1, 2)

        # start on a body different form the desired
        n.select_body(preferred=["excluded"])

        _, self.program = serialize_graph(graph)

        node_bodies, _, _ = generate_wiring(
            self.program,
            excluded_body_tags=["excluded"]
        )

        self.assertEqual(len(node_bodies), 1)
        asyncio.run(self.assert_tag_from_py_script(node_bodies[0], "func_1"))

    def test_select_preferred_excluded_node_body(self):

        with DeltaGraph() as graph:
            n = self.test_template.call(1, 2)

        # start on a body different form the desired
        n.select_body(preferred=["func_1"])

        _, self.program = serialize_graph(graph)

        node_bodies, _, _ = generate_wiring(
            self.program,
            preferred_body_tags=["preferred"],
            excluded_body_tags=["excluded"]
        )

        self.assertEqual(len(node_bodies), 1)
        asyncio.run(self.assert_tag_from_py_script(node_bodies[0], "func_2"))

    def test_selection_exclusion_preference(self):

        @DeltaBlock(
            template=self.test_template,
            allow_const=False,
            tags=["func_4", "excluded, preferred"]
        )
        def func_4(a: int, b: int) -> Void:
            print("func_4")
            raise DeltaRuntimeExit

        with DeltaGraph() as graph:
            n = self.test_template.call(1, 2)

        # start on a body different form the desired
        n.select_body(preferred=["func_4"])

        _, self.program = serialize_graph(graph)

        node_bodies, _, _ = generate_wiring(
            self.program,
            excluded_body_tags=["excluded"]
        )

        self.assertEqual(len(node_bodies), 1)
        asyncio.run(self.assert_tag_from_py_script(node_bodies[0], "func_1"))

        node_bodies, _, _ = generate_wiring(
            self.program,
            excluded_body_tags=["excluded"],
            preferred_body_tags=["preferred"]
        )

        self.assertEqual(len(node_bodies), 1)
        asyncio.run(self.assert_tag_from_py_script(node_bodies[0], "func_2"))

    def test_all_body_exclusion_error(self):

        with DeltaGraph() as graph:
            n = self.test_template.call(1, 2)

        _, self.program = serialize_graph(graph)

        with self.assertRaises(AttributeError):
            node_bodies, _, _ = generate_wiring(
                self.program,
                excluded_body_tags=["func_1", "func_2", "func_3"]
            )


if __name__ == "__main__":
    unittest.main()
