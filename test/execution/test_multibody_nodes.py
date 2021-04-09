import unittest

import deltalanguage as dl
from deltalanguage.test.execution import TestExecutionMultibodyNodes

from test.execution.base import TestExecutionBaseDS, PYSIMULATOR


class TestExecutionMultibodyNodesDS(TestExecutionBaseDS,
                                    TestExecutionMultibodyNodes):

    pass


if __name__ == "__main__":
    unittest.main()
