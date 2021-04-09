import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionConstantNodes

from test.execution.base import TestExecutionBaseDS, PYSIMULATOR


class TestExecutionConstantNodesDS(TestExecutionBaseDS,
                                   TestExecutionConstantNodes):

    pass


if __name__ == "__main__":
    unittest.main()
