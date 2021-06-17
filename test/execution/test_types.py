import unittest

import deltalanguage as dl
from deltalanguage.test.execution.test_types import TestExecutionTypes

from test.execution.base import TestExecutionBaseDS


class TestExecutionTypesDS(TestExecutionBaseDS,
                           TestExecutionTypes):

    @unittest.skip("DLANG1-289 fix float precision in both simulators")
    def test_primitives(self):
        pass


if __name__ == "__main__":
    unittest.main()
