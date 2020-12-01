import asyncio
import os
import sysconfig
import shlex
import logging

from find_libpython import find_libpython
from collections.abc import Iterable

from deltasimulator.build_tools import BuildArtifact, Environment
from deltasimulator.build_tools.utils import multiple_waits


log = logging.getLogger(__name__)


class CPPEnv(Environment):
    """Environment for running C++-related commands such as g++ and ar.

    .. note::
        Any stdout from these commands is written to :meth:`logging.debug`.
        Any stderr from them is written to :meth:`logging.warning`.
    """

    CFLAGS = ["-std=c++17",
              "-DSC_CPLUSPLUS=201703L",
              "-D_FORTIFY_SOURCE=2",
              "-faligned-new",
              "-fstack-protector",
              "-Wall", "-Wextra",
              # every warning but we use a lot of templated code so unused is common
              "-Wno-unused-variable", "-Wno-unused-parameter",
              "-Werror",
              "-g",
              "-grecord-gcc-switches",
              "-O2",
              "-fPIE"]

    async def _run_gcc(self, module_name: str, after):
        """Runs g++ on given module to compile to an object.

        Parameters
        ----------
        module_name : str
            The name of the module. Note that ".cpp" is appended by _run_gcc.
            We might change this behaviour if we end up compiling other things.
        after : list
            Coroutines to wait for before running g++. Typically for writing
            main and header files.

        Returns
        -------
        bool
            Returns True when complete.
        """
        await multiple_waits(after)
        log.info(f"contents of compile dir: {os.listdir(self.tempdir)}")

        cpp_path = os.path.join(self.tempdir, f"{module_name}.cpp")
        env_c_flags = sysconfig.get_config_var('CFLAGS')
        env_c_flags = shlex.split(env_c_flags)
        log.debug(f"CFLAGS: {env_c_flags}")

        cmd = ["g++",
                "-c",
                "-isystem/usr/local/systemc-2.3.3/lib-linux64",
                "-isystem/usr/local/systemc-2.3.3",
                "-isystem/usr/local/systemc-2.3.3/include",
                "-isystem/usr/local/share/verilator/include",
                f"-isystem/usr/local/include/python{sysconfig.get_python_version()}",
                f"-isystem{sysconfig.get_paths()['include']}",
                *env_c_flags,
                *self.CFLAGS,
                cpp_path,
                "-shared",
                "-o", f"{module_name}.o",
                ]

        log.info(f"running cmd {cmd}")
        proc = await asyncio.create_subprocess_exec(*cmd,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE,
                                                    cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        log.warning(stderr.decode("utf8"))
        if proc.returncode != 0:
            log.error(f"gcc failed with code {proc.returncode}")
            raise RuntimeError(f"gcc failed with code {proc.returncode}")

        return True

    def _get_o(self, module_name, after):
        """After gcc is run, the binary object file is returned.

        Parameters
        ----------
        module_name : str
            The name of the module. Note the .o file type will be
            appended to the string, so is not needed here.
        after : Coroutine
            Coroutine to wait for before the file is ready. Usually
            the process which builds the file.

        Returns
        -------
        BuildArtifact
            The module's binary object.
        """
        return BuildArtifact(f"{module_name}.o", env=self, after=after)

    async def _link(self, main, archive, after, name="main"):
        """Runs linker on main file, with archive.

        Parameters
        ----------
        main : str
            Main object file.
        archive : Union[BuildArtifact, list]
            Archive(s) of object files main is dependent on.
        after : list
            Coroutines to wait for before linking the objects.
        name : Optional[str]
            Name of final runtime, by default "main"

        Returns
        -------
        bool
            Returns True when complete.
        """

        if not isinstance(archive, Iterable):
            archives = [archive]
        else:
            archives = archive

        await multiple_waits(after)
        log.info(f"contents of link dir: {os.listdir(self.tempdir)}")

        main_path = os.path.join(self.tempdir, main)
        archive_paths = [os.path.join(self.tempdir, archive.name)
                         for archive in archives]
        log.info(f"linking: {main_path}, {archive_paths}")

        ld_flags = shlex.split(sysconfig.get_config_var('LDFLAGS'))
        cmd = ["g++",
               "-o",
               name,
               main_path,
               *archive_paths,
               f"-L{find_libpython()}",
               *ld_flags,
               "-L/usr/local/systemc-2.3.3/lib-linux64",
               "-lsystemc",
               "-lpython3.8",
               ]
        log.info(f"running cmd {cmd}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        log.warning(stderr.decode("utf8"))

        return True

    def _get_main(self, after, name="main"):
        """Gets main runtime binary.

        Parameters
        ----------
        after : Coroutine
            Coroutine to wait for before getting file.
        name : Optional[str]
            The name of the main runtime file, by default "main"

        Returns
        -------
        BuildArtifact
            The binary main runtime.
        """
        return BuildArtifact(name, self, after=after)

    async def _run_ar(self, objects, after, name="main"):
        """Runs ar to generate .a archive containing all object files.

        Parameters
        ----------
        objects : list
            Objects (.o file names) to put into the archive.
        after : list
            Coroutines to wait for before running the linker.
        name : Optional[str]
            Name of archive, by default "main"

        Returns
        -------
        bool
            Returns True when complete.
        """
        await multiple_waits(after)
        object_paths = [os.path.join(self.tempdir, object_name)
                        for object_name in objects]
        cmd = ["ar",
               "rcsT",
               f"{name}.a",
               *object_paths]
        log.info(f"running {cmd}")
        proc = await asyncio.create_subprocess_exec(*cmd,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE,
                                                    cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        log.warning(stderr.decode("utf8"))

        return True

    def _get_archive(self, after, name="main"):
        """Get the .a archive.

        Parameters
        ----------
        after : Coroutine
            Coroutine to wait for before the archive is ready.
        name : Optional[str]
            Name of the .a file, by default "main"

        Returns
        -------
        BuildArtifact
            The content of the .a file.
        """
        return BuildArtifact(f"{name}.a", self, after=after)

    async def _write_files(self, files):
        """Save files in the environment's temporary directory.

        Parameters
        ----------
        files : list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>`
            objects containing the files to save.

        Returns
        -------
        bool
            Returns True on completion.

        Raises
        ------
        AttributeError
            Raised if an item in files is not a BuildArtifact.
        """
        for buildartifact in files:
            try:
                with open(os.path.join(self.tempdir, buildartifact.name), "wb") as f:
                    data = await asyncio.wait_for(buildartifact.data, timeout=None)
                    f.write(data)
            except AttributeError:
                log.error(f"{buildartifact} is not a BuildArtifact")
                raise
        return True


    def compile(self, headers, cpp):
        """Compile the C++ file and return the resulting binary.

        Parameters
        ----------
        headers : list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects containing the required header files.
        cpp : BuildArtifact
            File containing the C++ code.

        Returns
        -------
        BuildArtifact
            The compiled binary object file.
        """
        input_files = self._write_files(headers+[cpp])
        top_name = cpp.name.split(".")[0]
        comp_flag = self._run_gcc(module_name=top_name, after=[input_files])
        return self._get_main(after=comp_flag, name=f"{top_name}.o")

    def archive(self, objects, name):
        """Generate archive file containing all binary objects.

        Parameters
        ----------
        objects : list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects containing the binary objects.
        name : str
            Name of the archive file. Note the .a file ending is appended.

        Returns
        -------
        BuildArtifact
            The content of the .a file.
        """
        input_files = self._write_files(objects)
        ar_flag = self._run_ar([o.name for o in objects], after=[
                               input_files], name=name)
        return self._get_main(after=ar_flag, name=f"{name}.a")

    def compile_and_link(self, headers, objects, main_cpp):
        """Run gcc to compile and link and produce a complete runtime binary.

        Parameters
        ----------
        headers : list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects containing the header files.
        objects : list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects containing the binary objects.
        main_cpp : BuildArtifact
            The C++ file for main.

        Returns
        -------
        BuildArtifact
            The main runtime binary.
        """
        input_files = self._write_files(headers+objects+[main_cpp])

        top_name = main_cpp.name.split(".")[0]
        comp_flag = self._run_gcc(module_name=top_name, after=[input_files])
        link_flag = self._link(
            top_name+".o", archive=objects, after=[comp_flag])
        main = BuildArtifact("main", env=self, after=link_flag)
        return main  # self._get_main(after=link_flag)
