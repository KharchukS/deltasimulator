import unittest
from deltasimulator.build_tools.cogify import cogify


class TestCogify(unittest.TestCase):

    def test_no_transformation(self):
        teststr = "hello, \n\0"
        result = cogify(teststr)
        self.assertEqual(result, teststr.encode("utf-8"))

    def test_block(self):
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
        teststr = """
        hello
        world"""
        result = cogify(teststr)
        resstr = b"\nhello\nworld"
        self.assertEqual(resstr, result)


if __name__ == "__main__":
    unittest.main()
