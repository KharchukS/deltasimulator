import glob
from os import path
import unittest

import deltalanguage as dl

from test.execution.base import TestExecutionBaseDS


class TestExecutionUnsorted(TestExecutionBaseDS):
    """These are the original tests difined in Deltasimulator which haven't
    been moved to any categories yet.

    TODO there 2 options for each of them:
    - find an appropriate category in ``deltalanguage.test.execution``
      so it runs on both simulators
    - if this test is specific for Deltasimulator, then it can be moved to
      a ``test.execution.test_deltasimulator.py``, thus such a tests
      is applicable only for this simulator.
    """

    def test_read_file(self):
        filename = path.join("test", "data", "test_add_64_bit.cpp")

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            with open(filename, "r") as txt_file:
                print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph("test_read_file") as graph:
            read_txt()

        self.check_executes_graph(graph, files=[filename])

    def test_read_multiple_files(self):
        filenames = [path.join("test", "data", "test_add_64_bit.cpp"),
                     path.join("test", "data", "test_add_64_bit.h")]

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            for filename in filenames:
                with open(filename, "r") as txt_file:
                    print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph() as graph:
            read_txt()

        self.check_executes_graph(graph, files=filenames)

    def test_read_pattern_files(self):
        pattern = path.join("test", "data", "test_add_*")

        @dl.DeltaBlock(allow_const=False)
        def read_txt() -> dl.Void:
            for filename in glob.glob(pattern):
                with open(filename, "r") as txt_file:
                    print(txt_file.read())
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph() as graph:
            read_txt()

        self.check_executes_graph(graph, files=[pattern])

    def test_python_file(self):
        from test.data.code_for_test import x

        @dl.DeltaBlock(allow_const=False)
        def run_code() -> dl.Void:
            print(x)
            raise dl.DeltaRuntimeExit

        with dl.DeltaGraph() as graph:
            run_code()

        files = [path.join("test", "data", "code_for_test.py"),
                 path.join("test", "__init__.py"),
                 path.join("test", "_utils.py")]

        self.check_executes_graph(graph, expect="5\n", files=files)

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

            with dl.DeltaGraph() as graph:
                print_cycles()

            serialized, _ = dl.serialize_graph(graph,
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

            with dl.DeltaGraph() as graph:
                print_cycles()

            serialized, _ = dl.serialize_graph(
                graph,
                name="dut",
                requirements=["permutation<=0.2.0",
                              "permutation==0.3.0"]
            )
            with open(df_filename, "wb") as df_file:
                df_file.write(serialized)

        else:
            self.check_executes_file(df_filename,
                                     exception=RuntimeError)

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
        """
        df_filename = path.join("test", "data", "constant.df")

        build_df_file = False
        if build_df_file:
            from permutation import Permutation

            @dl.DeltaBlock(allow_const=False)
            def num_cycles() -> dl.Int():
                return len(Permutation(2, 1, 4, 5, 3).to_cycles())

            s = dl.lib.StateSaver(int, verbose=True)

            with dl.DeltaGraph() as graph:
                s.save_and_exit(num_cycles())

            serialized, _ = dl.serialize_graph(graph,
                                               name="dut",
                                               requirements=["permutation"])

            with open(df_filename, "wb") as df_file:
                df_file.write(serialized)

        else:
            self.check_executes_file(df_filename,
                                     expect="saving 2\n",
                                     reqs=["permutation"])


if __name__ == "__main__":
    unittest.main()
