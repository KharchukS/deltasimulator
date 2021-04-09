import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionOptionalInputs

from test.execution.base import TestExecutionBaseDS, PYSIMULATOR


class TestExecutionOptionalInputsDS(TestExecutionBaseDS,
                                    TestExecutionOptionalInputs):

    pass


if __name__ == "__main__":
    unittest.main()
