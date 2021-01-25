"""Summary information about the package
    Attributes
    ----------
    __license__ : str
        Short description of our license.
    __copyright__ : str
        Copyright notice
    __url__ : str
        Project URL
    __contributors__ : str
        Single-line list of all project contributors.
    __contributors_lines__ : str
        Multi-line list of all project contributors.
    __email__ : str
        Contact email for the project.
    __version__ : str
        Package version in format ``<major>.<minor>.<micro>``
    __version_description__ : str
        Short description for the current version.
    __short_description__ : str
        Short summary of the package.
    __doc__ : Str
        Longer description of the package.
    __platforms__ : List[str]
        List of supported platforms
"""

__all__ = [
    "__license__",
    "__copyright__",
    "__url__",
    "__download_url__",
    "__docs_url__",
    "__contributors__",
    "__contributors_lines__",
    "__email__",
    "__version__",
    "__version_description__",
    "__short_description__",
    "__doc__",
    "__platforms__"
]

__license__ = "MIT License with Commons Clause"
__copyright__ = "Copyright (C) 2020 River Lane Research Ltd"


# Source URL
__url__ = "https://github.com/riverlane/deltasimulator"
# Package Hosting URL
__download_url__ = "https://pypi.org/project/deltasimulator/#files"
# Docs Hosting Url
__docs_url__ = "https://riverlane.github.io/deltasimulator"

contributors = ["Kenton Barnes",
                "Anton Buyskikh",
                "Marco Ghibaudi",
                "Alex Moylett",
                "Tom Parks",
                "Jan Snoeijs"]
__contributors__ = ", ".join(contributors)
__contributors_lines__ = "\n".join(contributors)
__email__ = "deltaflow@riverlane.com"

version_info = (0, 4, 0)
"""Tuple[int, int, int] : version information
The three components of the version:
``major``, ``minor`` and ``micro``: Module level variable documented inline.
"""
__version__ = ".".join(map(str, version_info[:3]))
__version_description__ = "Deltasimulator MVP Public Release."

__short_description__ = "Runs Deltaflow programs on virtual platforms"
__doc__ = """
    Deltasimulator is a build system developed by Riverlane. The system can be
    used to compile SystemC modules for nodes in a Deltaflow graph and wire the
    nodes up. From there a complete runtime executable can be compiled, or the
    graph can be connected to a larger platform representing physical devices
    such as the ARTIQ platform via a Hardware Abstraction Layer (HAL).
    """

__platforms__ = ['Ubuntu 20.04']
