import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionMultioutput

from test.execution.base import TestExecutionBaseDS


class TestExecutionMultioutputDS(TestExecutionBaseDS,
                                 TestExecutionMultioutput):

    pass


if __name__ == "__main__":
    unittest.main()
