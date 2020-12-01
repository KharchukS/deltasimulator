import tempfile


class Environment():
    """This base class supports defining a context manager providing
    access to build tools and a isolated enviroment.

    Attributes
    ----------

    tempdir : TemporaryDirectory
        The temporary directory this environment is within.
    """

    def __init__(self):
        self._tempdirmanger = tempfile.TemporaryDirectory()
        self.tempdir = None

        self._check_env_ok() # override this function to ensure all tools are present

    # I think we intend for the user to be making the contexts, so they will always
    # be created from non-async python. If we want to enter subcontexts we will need
    # __aenter__ as well.
    def __enter__(self):
        """enter the temp dir."""
        self.tempdir = self._tempdirmanger.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self._exit_info = (type, value, traceback)

    def __del__(self):
        type, value, traceback = self._exit_info
        self._tempdirmanger.__exit__(type, value, traceback)
        self.tempdir = None

    def _check_env_ok(self):
        """Overwritten by child environments to check the Environment has
        all the necessary tools.
        """
        return True
