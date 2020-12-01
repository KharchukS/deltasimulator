from deltasimulator.build_tools import Environment

class HostEnv(Environment):
    """A shim enviroment representing the host filesystem.

    Parameters
    ----------
    dir : str
        The path to the host directory.
    """

    def __init__(self, dir):
        self.tempdir = dir

    def __enter__(self):
        # nothing to do, as we don't need to isolate the host from itself.
        return self

    def __exit__(self, type, value, traceback):
        self._exit_info = (type, value, traceback)

    def __del__(self):
        self.tempdir = None
