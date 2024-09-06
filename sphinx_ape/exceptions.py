class SphinxApeException(Exception):
    """
    Base exception.
    """


class ApeDocsBuildError(SphinxApeException):
    """
    Building the docs failed.
    """


class ApeDocsTestError(SphinxApeException):
    """
    Running doc-tests failed.
    """


class ApeDocsPublishError(SphinxApeException):
    """
    Publishing the docs failed.
    """
