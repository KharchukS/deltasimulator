import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionPrimitives

from test.execution.base import TestExecutionBaseDS


class TestExecutionPrimitivesDS(TestExecutionBaseDS,
                                TestExecutionPrimitives):

    pass


if __name__ == "__main__":
    unittest.main()
