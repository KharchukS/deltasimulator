import unittest

import deltalanguage as dl
from deltalanguage.test.execution.test_types import TestExecutionTypes

from test.execution.base import TestExecutionBaseDS


class TestExecutionTypesDS(TestExecutionBaseDS,
                           TestExecutionTypes):

    pass


if __name__ == "__main__":
    unittest.main()
