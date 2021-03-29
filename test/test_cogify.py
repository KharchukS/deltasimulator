import unittest
from deltasimulator.build_tools.cogify import cogify


class TestCogify(unittest.TestCase):

    def test_no_transformation(self):
        teststr = "hello quantum world!"
        result = cogify(teststr)
        self.assertEqual(result, teststr.encode("utf-8"))

    def test_block(self):
        """This it how [[[cog<code>]]][[[end]]] code generation blocks work."""
        teststr = """
        #[[[cog
        #   for i in range(5):
        #       cog.outl(f"{i}")
        #]]]
        #[[[end]]]
        """
        result = cogify(teststr)
        resstr = b"\n0\n1\n2\n3\n4\n"
        self.assertEqual(resstr, result)

    def test_strip_tabs(self):
        """Remove tabs/whitespace identation in the beginning of all lines
        only if each line has them."""
        teststr = """
        hello
        world"""
        result = cogify(teststr)
        resstr = b"\nhello\nworld"
        self.assertEqual(resstr, result)


if __name__ == "__main__":
    unittest.main()
