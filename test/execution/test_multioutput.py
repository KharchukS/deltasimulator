import unittest

import deltalanguage as dl
from deltalanguage.test.execution import (
    TestExecutionSplittingSingleOutputNodeToSameNodeTest,
    TestExecutionSplittingSingleOutputNodeToDiffNodesTest,
    TestExecutionSplittingMultiOutputNodeTest
)

from test.execution.base import TestExecutionBaseDS


class TestExecutionSplittingSingleOutputNodeToSameNodeTestDS(
    TestExecutionBaseDS,
    TestExecutionSplittingSingleOutputNodeToSameNodeTest
):
    pass



class TestExecutionSplittingSingleOutputNodeToDiffNodesTestDS(
    TestExecutionBaseDS,
    TestExecutionSplittingSingleOutputNodeToDiffNodesTest
):
    pass



class TestExecutionSplittingMultiOutputNodeTestDS(
    TestExecutionBaseDS,
    TestExecutionSplittingMultiOutputNodeTest
):
    pass



if __name__ == "__main__":
    unittest.main()
