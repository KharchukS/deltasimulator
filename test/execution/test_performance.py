import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionPerformance

from test.execution.base import TestExecutionBaseDS


class TestExecutionPerformanceDS(TestExecutionBaseDS,
                                 TestExecutionPerformance):

    pass


if __name__ == "__main__":
    unittest.main()
