import glob
from os import path, chmod, environ
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest

import deltalanguage as dl

from deltasimulator.lib import build_graph


class TestExecutionBaseDS(unittest.TestCase):
    """Test execution base for Deltasimulator, defines method for executing
    and checking test graphs.
    """

    def setUp(self):
        dl.DeltaGraph.clean_stack()
        self.files = []
        self.reqs = []
        self.maxDiff = None
        self.sysc_output_prefix = ""
        self.sysc_output_suffix = textwrap.dedent(
            """\
            
            Info: /OSCI/SystemC: Simulation stopped by user.
            Completed!
            """
        )

    def tearDown(self):
        for file in self.files:
            shutil.move(f"{file}_temp", file)
        for req in self.reqs:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', req])

    def check_executes_graph(self, graph, expect=None, files=[], reqs=[],
                             exception=None, excluded_body_tags=None,
                             preferred_body_tags=None):
        _, program = dl.serialize_graph(graph, name="dut", files=files)
        self.check_executes(program, expect=expect, files=files, reqs=reqs,
                            exception=exception, 
                            excluded_body_tags=excluded_body_tags, 
                            preferred_body_tags=preferred_body_tags)

    def check_executes_file(self, file, expect=None, files=[], reqs=[],
                            exception=None, excluded_body_tags=None,
                            preferred_body_tags=None):
        with open(file, "rb") as df_file:
            program = dl.deserialize_graph(df_file.read())
        self.check_executes(program, expect=expect, files=files, reqs=reqs,
                            exception=exception, 
                            excluded_body_tags=excluded_body_tags, 
                            preferred_body_tags=preferred_body_tags)

    def check_executes(self, program, expect: str = None, files=[], reqs=[],
                       exception=None, excluded_body_tags=None,
                       preferred_body_tags=None):
        """Build SystemC program and executes them in temp directory.

        Parameters
        ----------
        expect : str
            Should contain the exact multistring expression we expect on
            stdout, excluding both SystemC prefix and postfix.
        exception : Exception
            Exception thrown by the simulator at _any_ stage
            (includes building, deployment, execution, etc.).
        excluded_body_tags
            Body tags to exclude.
        preferred_body_tags
            Body tags to prefer.
        """
        self.files = set([file
                          for pattern in files
                          for file in glob.glob(pattern)])
        for file in self.files:
            shutil.move(file, f"{file}_temp")
        shutil.rmtree("__pycache__", ignore_errors=True)
        self.reqs = reqs

        with TemporaryDirectory() as build_dir:
            try:
                build_graph(
                    program,
                    main_cpp=path.join(path.dirname(__file__),
                                       "main.cpp"),
                    build_dir=build_dir, 
                    excluded_body_tags=excluded_body_tags,
                    preferred_body_tags=preferred_body_tags
                )

            except Exception as e:
                if exception is not None and isinstance(e, exception):
                    print("Expected error caught on the building stage")
                    return
                print("Unexpected error caught on the building stage")
                print(sys.exc_info()[0])
                raise

            # Setting the permission to run the file
            chmod(f"{build_dir}/main", 0o777)

            try:
                # We disable the SYSTEMC Banner to clear the output by setting
                # SYSTEMC_DISABLE_COPYRIGHT_MESSAGE
                env = dict(environ, SYSTEMC_DISABLE_COPYRIGHT_MESSAGE="1")
                _proc = subprocess.run("./main",
                                       cwd=build_dir,
                                       shell=True,
                                       check=True,
                                       stdout=subprocess.PIPE,
                                       env=env)

            except subprocess.CalledProcessError as e:
                if exception == RuntimeError:
                    self.assertEqual(e.returncode, 255)
                    print("Expected error caught on the execution stage")
                else:
                    print("Unexpected error caught on the execution stage")
                    print(f"{e.returncode} - {e.output}")
                    raise e

            except:
                print("Unexpected error caught on the execution stage")
                print(sys.exc_info()[0])
                raise

            if expect:
                output_full = _proc.stdout.decode()

                # remove Deltasimulator specific lines:
                output_list = [line
                               for line in output_full.split('\n')
                               if not '_module::PyInit_sysc() called ' in line]

                self.assertMultiLineEqual(
                    '\n'.join(output_list),
                    self.sysc_output_prefix +
                    textwrap.dedent(expect) +
                    self.sysc_output_suffix
                )
