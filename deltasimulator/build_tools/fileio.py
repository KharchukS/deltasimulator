from deltasimulator.build_tools.utils import wait
import asyncio
import os.path
import os
import traceback
import logging
log = logging.getLogger(__name__)


class BuildArtifact():
    """Wrapper object for asynchronously building a file.

    Parameters
    ----------
    name : str
        The name of the artifact. Typically the file name.
    env : Optional[Environment]
        The environment that the artifact was built within. This is used
        to know which temporary directory the artifact is within.
        By default `None`.
    path : Optional[str]
        The file path within the temp directory, by default "."
    after : Optional[Coroutine]
        An asynchronous coroutine which needs to complete before the artifact
        has been built
    data : Union[bytes, bytearray]
        If the artefact's content is already available then it can be
        provided as-is rather than needing to build it in an environment.


    .. warning::
        If `env` is `None` then `data` must not be `None`,
        otherwise a :exc:`ValueError` will be raised.

    .. warning::
        If `data` is provided then it must be bytes or byteslike,
        otherwise a :exc:`TypeError` will be raised.
    """

    def __init__(self, name: str, env=None, path: str = ".", after=None, data=None):
        self.name = name
        self.path = path

        if data is not None: # literal provided
            if not isinstance(data, (bytes, bytearray)):
                raise TypeError(
                    f"If data is provided it must be bytes or byteslike, was {type(data)}")
            self._data = data  # if we have bytes, use them
            self.env = None
            self._flag = None
        else:  # no data - need to look it up in an env
            self._data = None
            if env is None:
                raise ValueError(
                    "If data is not provided, we must know the env to look the file up within")
            self.env = env
            if env.tempdir is None:
                raise RuntimeError(
                    f"env {env} does not have a tempdir for path lookup")
            # flag is a coro that when completed, indicates
            # the file is available to be read
            self._flag = after

    @property
    async def data(self):
        """The content of the :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>`.
        If data was not provided when constructed then the content is
        retrieved from the build environment's temporary directory,
        building the file if needed by waiting for the :class:`Coroutine`
        to complete.

        Returns
        -------
        bytes
            The content of the artifact.

        Raises
        ------
        RuntimeError
            If there is no data and no :class:`Environment` is provided
            then an error will be raised.
        FileNotFoundError
            Raised if the file wrapped by the BuildArtifact is not found.
            This might be because there was an error during the build process
            which resulted in the file not being created.
        """
        if self._data is not None:
            return self._data
        else:
            if self._flag is not None:
                await wait(self._flag)
                log.debug(f"flag {self._flag} resolved")
            if self.env.tempdir is None:
                raise RuntimeError(
                    f"env {self.env} does not have a tempdir for path lookup")
            try:
                path = os.path.join(self.env.tempdir, self.path, self.name)
                with open(path, "rb") as file:
                    self._data = file.read()
                    return self._data
            except FileNotFoundError as e:
                # try and be helpful
                log.error(
                    f"file lookup failed: dir contents {list(os.walk(path))}, {e}")
                log.error(
                    f"tmp dir root contents {os.listdir(self.env.tempdir)}, {e}")
                log.error(
                    f"you probably forgot a after call - we expect to be after {self._flag}, {e}")
                log.error(f"Full traceback: {traceback.format_exc()}, {e}")

                # we currently hold a ref to env, that will preserve the tempdirs
                # that should hold this file. We can be helpful and drop to a shell
                # so the user can investigate the problem
                if False:
                    log.error(
                        "Dropping to a shell, press CTRL+d to exit and continue")
                    os.chdir(self.env.tempdir)
                    import pty
                    pty.spawn("/bin/bash")

                # after the shell is done, the user has investigated the problem
                # we should just terminate the process
                raise


class BuildArtifactSet():
    """Wrapper object for asynchronously building a set of files.

    A :class:`BuildArtifactSet` has the same API as a :class:`dict` object in Python.
    """

    def __init__(self):
        self._store = dict()

    async def __getitem__(self, key, type=None):
        print(self._store)
        return await self._store.__getitem__(key)

    async def __setitem__(self, key, value):
        # value = await asyncio.wait_for(value, timeout=None)
        self._store.__setitem__(key, value)


async def write_futures(object: BuildArtifact, output_file):
    """Asynchronously write the contents of the BuildArtifact to file. 
    Use if already within an async coroutine.

    Parameters
    ----------
    object : BuildArtifact
        The artifact to be written.
    output_file
        The file to be written to.
    """
    try:
        data = await asyncio.wait_for(object.data, timeout=None)
    except AttributeError:
        log.error(f"failed to write {object}")
        raise
    output_file.write(data)


def write(object: BuildArtifact, output_file):
    """Asynchronously write the contents of the BuildArtifact to file. 

    Parameters
    ----------
    object : BuildArtifact
        The artifact to be written.
    output_file
        The file to be written to.


    .. warning::
        Will raise an error if called within an asynchronous process.
        Use :meth:`write_futures` instead.
    """

    asyncio.run(write_futures(object, output_file))
