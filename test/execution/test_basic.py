import unittest

import deltalanguage as dl
from deltalanguage.test.execution import (TestExecutionPyFuncBody,
                                          TestExecutionPyInteractiveBody,
                                          TestExecutionPyInteractiveBodySend,
                                          TestExecutionPyMigenBody,
                                          TestExecutionGeneral)

from test.execution.base import TestExecutionBaseDS


class TestExecutionPyFuncBodyDS(TestExecutionBaseDS,
                                TestExecutionPyFuncBody):

    pass


class TestExecutionPyInteractiveBodyDS(TestExecutionBaseDS,
                                       TestExecutionPyInteractiveBody):

    pass


class TestExecutionPyInteractiveBodySendDS(TestExecutionBaseDS,
                                           TestExecutionPyInteractiveBodySend):

    pass


class TestExecutionPyMigenBodyDS(TestExecutionBaseDS,
                                 TestExecutionPyMigenBody):

    @unittest.skip("DL test needs updating for latest simulator changes.")
    def test_PyMigenBody(self):
        pass

    @unittest.skip("DLANG1-298")
    def test_migen_trigger_fails(self):
        pass

    @unittest.skip("DLANG1-298")
    def test_migen_trigger_succeeds(self):
        pass

    @unittest.skip("DLANG1-291")
    def test_one_migen_node_with_separate_ctrl_on_output_valid(self):
        pass


class TestExecutionGeneralDS(TestExecutionBaseDS,
                             TestExecutionGeneral):

    pass


if __name__ == "__main__":
    unittest.main()
