import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionBasic

from test.execution.base import TestExecutionBaseDS, PYSIMULATOR


class TestExecutionBasicDS(TestExecutionBaseDS,
                           TestExecutionBasic):

    @unittest.skip("DL test needs updating for latest simulator changes.")
    def test_PyMigenBody(self):
        pass


if __name__ == "__main__":
    unittest.main()
