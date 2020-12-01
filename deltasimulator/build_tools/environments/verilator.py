import asyncio
from itertools import zip_longest
import logging
import os
import re
import subprocess as sp
import traceback

import dill

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
from deltasimulator.build_tools import Environment, BuildArtifact
from deltasimulator.build_tools.utils import wait

log = logging.getLogger(__name__)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.
    Taken from :py:mod:`itertools` recipes.
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class VerilatorEnv(Environment):
    """Environment for running Verilator to generate SystemC modules of
    Migen nodes.

    .. note::
        Migen nodes communicate using three signals:

        - a data signal which the data is sent along,

        - a valid signal to indicate that there is data to be sent,

        - a ready signal to indicate that the node is ready to receive data.

    Attributes
    ----------

    env_ok
        Set once to ensure the environment is okay to run.


    .. warning::
        Verilator 4.0 or greater is required for the environment to run.

    """

    env_ok = None  # only check once per Env (performance)

    def _check_env_ok(self):
        """Checks that the environment is able to run.

        Returns
        -------
        bool
            True if the environment is okay.

        Raises
        ------
        RuntimeError
            Raised if Verilator version is earlier than 4.0 or if any other
            exception is raised while checking the version.
        """
        if self.env_ok is not None:
            if not self.env_ok:
                raise RuntimeError("env not ok from previous check")
            else:
                return self.env_ok
        else:
            # do real checking
            try:
                output = sp.run(["verilator", "--version"],
                                capture_output=True,
                                check=True)
                version = output.stdout.split(b" ")[1]
                if float(version) < 4.0:
                    raise RuntimeError(
                        f"verilator version too old, need >4 got {version}")
            except Exception as ex:
                traceback.print_exc()
                raise RuntimeError(
                    f"failed to check enviroment, got error {ex}") from ex
            else:
                self.env_ok = True

    async def _run_verilator(self, top_v: BuildArtifact):
        """This process builds a top.v into a cpp file. First step.
        -${DRUN} verilator -CFLAGS "${CPPFLAGS}" --sc $< \
                           --Mdir build/verilated/  \
                               --top-module $(basename $(notdir $<)) \
                                -I$(dir $<) \
                                -Wno-lint

        Parameters
        ----------
        top_v: BuildArtifact
            The Verilog code for the module.


        .. warning::
            `top_v` is expected to have the same name as its module.
            If this is not the case then the module name will be replaced.

        .. warning::
            ROM init blocks are not supported by Verilator. In the Verilog
            contains an init block then the init files are written separately.
        """
        data = await asyncio.wait_for(top_v.data, timeout=None)
        mod_name = top_v.name.split(".")[0].encode("utf8")

        # verify the module name is correct
        name_regex = b'module\\s+([a-zA-Z0-9\\_]+)\\('
        mod_internal_name = re.search(name_regex, data)[1]  # first subgroup
        if mod_internal_name != mod_name:
            log.warning(
                "WARNING: migen node name doesn't match its module name"
                f"This is not supported! expected: {mod_name},"
                f"got: {mod_internal_name}"
            )
            data = re.sub(name_regex, b"module " +
                          mod_name+b"(", data)

        # look for inline ROM init files!
        # verilator does not suppport this, so we need to write them seperately
        module_regex = b"([a-zA-Z0-9\\_]+)\\.init:\n"
        matches = re.split(module_regex, data)
        if len(matches) > 1:
            for rom_name, rom_data in grouper(matches[1:], 2):
                log.info(
                    "INFO: found a ROM init block called"
                    f"{rom_name} in {mod_name}"
                    "This is not supported by Verilator."
                    "Extracting the data by hand."
                )
                full_string = (
                    f'{rom_name.decode("utf-8")}.init:'
                    f'\n{rom_data.decode("utf-8")}'
                ).encode("utf-8")
                # remove the ROM data from the file
                data = data.replace(full_string, b'')
                init_file = f"{rom_name.decode('utf-8')}.init"
                fpath = os.path.join(self.tempdir, init_file)
                with open(fpath, "wb") as f:
                    f.write(rom_data)
                log.info(f"wrote {len(rom_data)} bytes to {rom_name}.init")
                print(rom_data)

        with open(os.path.join(self.tempdir, top_v.name), "wb") as f:
            f.write(data)

        # run the build step!
        log.info("running build")
        cmd = ["verilator",
               "--sc", top_v.name,  # build a module for SystemC
               "--top-module", top_v.name.split(".")[0],
               "-CFLAGS", "-std=c++17 -DSC_CPLUSPLUS=201703L \
                   -D_FORTIFY_SOURCE=2 -faligned-new -fstack-protector \
                        -Wall -Werror -g -grecord-gcc-switches -O2",
               "-Wno-fatal", "-Wno-combdly", "-Wno-unoptflat",
               "-Wno-width", "-Wno-initialdly",
               # ensure consistant port types by making everything a bv
               "--pins-bv", "1"
               ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        log.warning(stderr.decode("utf8"))
        return True

    def _get_cpp(self, top_v, after):
        """Returns the C++ file generated by Verilator.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code.
        after : Coroutine
            Process to wait for before the C++ code is ready.

        Returns
        -------
        BuildArtifact
            The C++ code generated.
        """
        mod_name = top_v.name.split(".")[0]
        cpp_name = "V"+mod_name+".cpp"
        cpp_path = "obj_dir"
        return BuildArtifact(
            name=cpp_name,
            path=cpp_path,
            after=after,
            env=self
        )

    def _get_h(self, top_v, after):
        """Get the header file generated by Verilator.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code.
        after : Coroutine
            Process to wait for before the header file is generated.

        Returns
        -------
        BuildArtifact
            The generated header file.
        """
        mod_name = top_v.name.split(".")[0]
        h_name = "V"+mod_name+".h"
        h_path = "obj_dir"
        return BuildArtifact(
            name=h_name,
            path=h_path,
            after=after,
            env=self
        )

    def _get_rom_init(self, top_v, after):
        """Check if there are any ROM init files and if so return them.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code.
        after : Coroutine
            Process which builds the Verilated code.

        Returns
        -------
        list
            :class:`BuildArtifact<deltasimulator.build_tools.BuildArtifact>`
            objects for the ROM init files.
        """
        # Get the Verilog code and search for ROM init code by regex.
        # TODO: Find a nicer way of getting the init file name.
        data = asyncio.run(top_v.data)
        module_regex = b"([a-zA-Z0-9\\_]+)\\.init:\n"
        inits = []
        for match in re.finditer(module_regex, data):
            rom_name = match[0][:-2].decode("utf8")
            inits.append(BuildArtifact(
                name=rom_name,
                env=self,
                after=after
            ))
        return inits

    async def _build_objects(self, top_v, h, after):
        """Once C++ and header files are generated, use make to compile them
        into a .a archive.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code. Only the file name is used here.
        h : BuildArtifact
            The header file generated.
        after : Coroutine
            Code can be compiled after this :class:`Coroutine` has finished.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        # given _build_Vcpp has run in tempdir, use make to build the
        # required object files.
        # we could possibly get a little more parallelism here by doing each
        # target individually.

        # we don't need the file, just the name
        # import code; from pprint import pprint;
        # vp=lambda obj: pprint(vars(obj)); code.interact(local=locals())

        # ensure .cpp is present by waiting for flag
        await wait(after)
        log.debug(
            f"verilator env before object build {os.listdir(self.tempdir)}")
        mod_name = top_v.name.split(".")[0]

        proc = await asyncio.create_subprocess_exec(
            "make", "-C", "obj_dir/", "-j", "-f", "V" +
            mod_name+".mk", "V"+mod_name+"__ALL.a",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        if stderr:
            log.warning(stderr.decode("utf8"))
        log.info(
            f"{os.listdir(self.tempdir)},"
            f"{os.listdir(os.path.join(self.tempdir, 'obj_dir'))}"
        )
        return True

    async def _build_verilated_o(self, top_v, after):
        """Build the verilated.o binary file.
        This is required when linking nodes which were built using Verilator.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code. Only the file name is used here.
        after : Coroutine
            :class:`Coroutine` that needs to finish before the verilated.o
            file can be built.

        Returns
        -------
        bool
            Returns True upon completion.
        """
        await wait(after)
        mod_name = top_v.name.split(".")[0]

        proc = await asyncio.create_subprocess_exec(
            "make", "-C", "obj_dir/", "-j", "-f",
            "V"+mod_name+".mk", "verilated.o",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.tempdir)

        stdout, stderr = await proc.communicate()
        log.info(stdout.decode("utf8"))
        if stderr:
            log.warning(stderr.decode("utf8"))
        return True

    def _get_verilated_o(self, after):
        """Once verilated.o is built, return the file.

        Parameters
        ----------
        after : Coroutine
            :class:`Coroutine` which is building the verilated.o file.

        Returns
        -------
        BuildArtifact
            The verilated.o binary object.
        """
        return BuildArtifact(
            name="verilated.o",
            path="obj_dir/",
            env=self,
            after=after
        )

    def _get_ALL_a(self, top_v, after):
        """Once the binary objects have been built return them in a .a archive.

        Parameters
        ----------
        top_v : BuildArtifact
            Verilog code file. Only used for the file name.
        after : Coroutine
            :class:`Coroutine` which builds the binary objects.

        Returns
        -------
        BuildArtifact
            The binary objects in a .a archive.
        """
        mod_name = top_v.name.split(".")[0]
        h_name = "V"+mod_name+"__ALL.a"
        h_path = "obj_dir"
        return BuildArtifact(
            name=h_name,
            path=h_path,
            env=self,
            after=after
        )

    # def _get_verilated_sc_h(self):
    #     this is just in the same dir as verilator.
    #     path = sp.run(["which", "verilator"],
    #       capture_output=true, check=True).stdout
    #     return BuildArtifact(name="verilated_sc.h",
    #       path="obj", env=self, after=None)
    # TODO: use this rather than letting cxxenv look for headers

    def verilate(self, top_v: BuildArtifact):
        """Runs Verilator and builds the binary objects.

        Parameters
        ----------
        top_v : BuildArtifact
            The Verilog code.

        Returns
        -------
        dict
            A map of strings to :class:
            `BuildArtifact<deltasimulator.build_tools.BuildArtifact>` objects:

            - "cpp": the C++ file
            - "h": the header file
            - "init": list of ROM init files
            - "ALL.a": the .a archive containing the binary objects
            - "verilated.o": the verilated.o binary object
        """
        # fist step: generate a simulation module
        verilated = self._run_verilator(top_v)
        cpp = self._get_cpp(top_v, after=verilated)
        h = self._get_h(top_v, after=verilated)

        # second step: compile the top.cpp into a shared object
        binary = self._build_objects(top_v, h, after=verilated)
        all_a = self._get_ALL_a(top_v, after=binary)

        # return a set of build artifacts
        built_artifacts = dict()
        built_artifacts["cpp"] = cpp
        built_artifacts["h"] = h
        built_artifacts["init"] = self._get_rom_init(
            top_v=top_v, after=verilated)
        built_artifacts["ALL.a"] = all_a
        built_artifacts["verilated.o"] = self._get_verilated_o(
            after=self._build_verilated_o(top_v, after=verilated))
        # built_artifacts["verilated_sc.h"] =
        #   self._get_verilated_sc_h(after=binary)
        return built_artifacts

    @staticmethod
    def as_c_type(df_type):
        """Gives the SystemC equivalent of the given type.

        Parameters
        ----------
        df_type : bytes
            The dill serialisation of the DeltaType.

        Returns
        -------
        str
            String of the SystemC equivalent.


        .. note::
            PyMigenNode is a subclass of PythonNode and
            uses the same data_types for I/O ports.
            For type format see :meth:`PythonatorEnv.as_c_type`.
        """
        return f"sc_bv<{dill.loads(df_type).size}>"

    @staticmethod
    def get_sysc_port_name(port, direction="out") -> tuple:
        """Get the wire names for a Migen node's ports.

        Parameters
        ----------
        port
            capnp object describing the port.
        direction : Optional[str]
            The direction of the port, by default "out"

        Returns
        -------
        tuple
            Names for the data, valid and ready wires.
            Format for wire names is `{port.name}_{direction}_{type}`,
            where `port_name` is the name of the port,
            `direction` is "out" or "in" and `type` is "data", "valid"
            or "ready".


        .. note::
            The direction of the ready wire is the opposite of the direction
            of the data and valid wires.
        """
        if direction == "out":
            return (
                f"{port.name}_out_data",
                f"{port.name}_out_valid",
                f"{port.name}_in_ready"
            )
        elif direction == "in":
            return (
                f"{port.name}_in_data",
                f"{port.name}_in_valid",
                f"{port.name}_out_ready"
            )

    @staticmethod
    def get_port_output(port, direction="out"):
        """Get the name of the port's data wire.

        Parameters
        ----------
        port
            capnp object describing the port.
        direction : Optional[str]
            The direction of the port, by default "out"

        Returns
        -------
        str
            Name for the port's data wire.
            See :meth:`VerilatorEnv.get_sysc_port_name` for the naming format.
        """
        if direction == "out":
            return f"{port.name}_out_data"
        elif direction == "in":
            return f"{port.name}_in_data"

    @staticmethod
    def get_port_valid(port, direction="out"):
        """Get the name of the port's valid wire.

        Parameters
        ----------
        port
            capnp object describing the port.
        direction : Optional[str]
            The direction of the port, by default "out"

        Returns
        -------
        str
            Name for the port's valid wire.
            See :meth:`VerilatorEnv.get_sysc_port_name` for the naming format.
        """
        if direction == "out":
            return f"{port.name}_out_valid"
        elif direction == "in":
            return f"{port.name}_in_valid"

    @staticmethod
    def get_port_ready(port, direction="out"):
        """Get the name of the port's ready wire.

        Parameters
        ----------
        port
            capnp object describing the port.
        direction : Optional[str]
            The direction of the port, by default "out"

        Returns
        -------
        str
            Name for the port's ready wire.
            See :meth:`VerilatorEnv.get_sysc_port_name` for the naming format.
        """
        if direction == "out":
            return f"{port.name}_in_ready"
        elif direction == "in":
            return f"{port.name}_out_ready"

    @staticmethod
    def get_module_name(top_p):
        """Get the name of the SystemC module for a Migen node.

        Parameters
        ----------
        top_p
            capnp object describing the Migen node.

        Returns
        -------
        str
            The name of the Migen node's SystemC module.
            The format is `V{node_name}` where `node_name`
            is the name of the node.
        """
        return "V"+top_p.name
