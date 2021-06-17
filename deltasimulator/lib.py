import asyncio
import dill
from os import path
from typing import List
import subprocess
import sys
import zipfile

from deltasimulator.build_tools import BuildArtifact, write
from deltasimulator.build_tools.environments import (PythonatorEnv,
                                                     VerilatorEnv,
                                                     WiringEnv,
                                                     CPPEnv,
                                                     HostEnv)
from capnp.lib.capnp import _DynamicStructBuilder


def generate_wiring(
    program: _DynamicStructBuilder,
    excluded_body_tags: List[object] = None,
    preferred_body_tags: List[object] = None
):
    """Creates the wiring of the nodes defined in a program.

    Parameters
    ----------
    program: _DynamicStructBuilder
        A Deltaflow serialized graph.
    excluded_body_tags : typing.List[object]
        typing.List of keys to exclude from selection
    preferred_body_tags : typing.List[object]
        typing.List of keys to be preferred for selection if available

    Returns
    -------
    node_bodies: list
        The bodies of the extracted nodes.
    node_inits: list
        All the ROM files found in the migen nodes, extracted as strings.
        This solves an incompatibility between some migen generated outputs
        and verilator.
    wiring: dict
        The graph wiring, used to generate a SystemC top
        level to wire the graph.
    """
    node_headers = []
    node_bodies = []
    node_modules = []
    node_objects = []
    node_inits = []
    exclusions = excluded_body_tags if excluded_body_tags is not None else []
    preferred = preferred_body_tags if preferred_body_tags is not None else []
    verilated_o = None

    exclusions = set(excluded_body_tags if excluded_body_tags is not None else [])
    preferred = set(preferred_body_tags if preferred_body_tags is not None else [])

    selected_node_bodies = []
    for node in program.nodes:
        body_id = None
        if node.bodies:
            # If there are no node.bodies then it is what was previously
            # called a template node and cannot be pythonated

            not_excluded_list = []
            for body_id in node.bodies:
                # If body has no excluded tag
                body_tags = set(dill.loads(program.bodies[body_id].tags))
                if not exclusions & body_tags:
                    not_excluded_list.append(body_id)

            if not_excluded_list:
                for body_id in not_excluded_list:
                    # If body has a preferred tag
                    body_tags = set(dill.loads(program.bodies[body_id].tags))
                    if preferred & body_tags:
                        break  # use the first body_id where there is a match
                else:
                    body_id = not_excluded_list[0]
            else:
                raise AttributeError(
                    f"All usable bodies for node '{node.name}' have been excluded!"
                )

            which_body = program.bodies[body_id].which()

            if which_body in ['python', 'interactive']:
                with PythonatorEnv(program.bodies) as env:
                    build_artifacts = env.pythonate(node, body_id)
                    node_headers.append(build_artifacts["h"])
                    if "py" in build_artifacts:
                        node_bodies.append(build_artifacts["py"])
                    node_modules.append(build_artifacts["cpp"])
                    node_objects.append(build_artifacts["o"])

            elif which_body == 'migen':
                # This part is adopted from initial-example:
                top_v = BuildArtifact(
                    name=f"{node.name}.v",
                    data=program.bodies[body_id].migen.verilog.encode("utf8")
                )

                with VerilatorEnv() as env:
                    build_artifacts = env.verilate(top_v)

                node_headers.append(build_artifacts["h"])
                node_modules.append(build_artifacts["cpp"])
                node_objects.append(build_artifacts["ALL.a"])
                node_inits += build_artifacts["init"]
                if not verilated_o:
                    verilated_o = build_artifacts["verilated.o"]

        selected_node_bodies.append(body_id)

    with WiringEnv(program.nodes,
                   selected_node_bodies,
                   program.bodies,
                   node_headers,
                   node_objects,
                   verilated_o,
                   program.name) as env:
        wiring = env.wiring(program.graph)

    return node_bodies, node_inits, wiring


async def _wait_for_build(wiring: dict):
    """Waits for all the objects associated with the wiring to be
    ready.

    Parameters
    ----------
    wiring
        A wired graph.
    """
    for comp in wiring:
        await asyncio.wait_for(wiring[comp].data, timeout=None)


def _copy_artifacts(main, inits, node_bodies, destination):
    """Copies all the required artifacts into a new destination.

    Parameters
    ----------
    main
        Main file (main.cpp) for the graph.
    inits
        Memory configuration files.
    node_bodies
        Content of the nodes.
    destination
        Folder to copy the artifacts into. Note: created if it does
        not exists.
    """
    for init in inits:
        with open(path.join(destination, init.name), "wb") as f:
            write(init, f)

    for body in node_bodies:
        with open(path.join(destination, body.name), "wb") as f:
            write(body, f)

    with open(path.join(destination, "main"), "wb") as f:
        write(main, f)


def _compile_and_link(program_name: str, wiring: list, main_cpp: str):
    """Compiles and link the graph together with a provided top
    level file.

    Parameters
    ----------
    program_name: str
        Name of the program to generate.
    wiring: list
        Wired graph generated via cog.
    main_cpp: str
        Top level main file.
    """
    asyncio.run(_wait_for_build(wiring))
    _main_h = wiring[program_name + ".h"]
    _main_a = wiring[program_name + ".a"]

    # Converting the main.cpp into a BuildArtifact
    with HostEnv(dir=path.dirname(main_cpp)) as env:
        _main_cpp = BuildArtifact(name=path.basename(main_cpp), env=env)

    with CPPEnv() as cpp:
        main = cpp.compile_and_link(
            [_main_h],
            [_main_a],
            _main_cpp
        )

    return main


def build_graph(
    program: _DynamicStructBuilder,
    main_cpp: str,
    build_dir: str,
    excluded_body_tags: List[object] = None,
    preferred_body_tags: List[object] = None
):
    """Generates an executable to be stored in a build directory.

    Parameters
    ----------
    program: _DynamicStructBuilder
        The Deltaflow program to be converted into SystemC.
    main_cpp: str
        SystemC top level file that starts the SystemC simulation and
        defines an implementation for eventual templatedNodes.
    build_dir: str
        The target directory in which to store the output.
    excluded_body_tags : typing.List[object]
        typing.List of keys to exclude from selection
    preferred_body_tags : typing.List[object]
        typing.List of keys to be preferred for selection if available

    Examples
    --------
    The *main.cpp* (other filenames are allowed) should at least contain the
    following:

    .. code-block:: c++

        #include <systemc>
        #include <Python.h>
        #include "dut.h"
        using namespace sc_dt;
        int sc_main(__attribute__(int argc, char** argv) {
            Py_UnbufferedStdioFlag = 1;
            Py_Initialize();
            sc_trace_file *Tf = nullptr;
            sc_clock clk("clk", sc_time(1, SC_NS));
            sc_signal<bool> rst;
            // Dut is the name you
            Dut dut("Dut", Tf);
            dut.clk.bind(clk);
            dut.rst.bind(rst);
            rst.write(0);
            sc_start(1000, SC_NS);
            return 0;
        }


    With the associate Python code:

    .. code-block:: python

        import deltalanguage as dl
        from deltasimulator.lib import build_graph
        ...
        _, program = dl.serialize_graph(graph, name="dut")
        build_graph(program, main_cpp="main.cpp",
             build_dir="/workdir/build")
        ...


    .. todo::

        Setting stdio/stderr to not buffer is required because `Py_Finalize`
        can cause some memory errors (with eg the Qiskit HAL test).
        Is there a fix for this?
    """

    if len(program.requirements) > 0:
        req_path = path.join(build_dir, "requirements.txt")
        with open(req_path, "w") as req_txt:
            req_txt.write("\n".join(program.requirements))

        try:
            subprocess.run([sys.executable,
                            '-m',
                            'pip',
                            'install',
                            '-r',
                            req_path],
                           capture_output=True,
                           check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Error with installing required dependencies:",
                               e.output) from e
    
    try: 
        node_bodies, node_inits, wiring = generate_wiring(
            program, excluded_body_tags, preferred_body_tags
        )
    except AttributeError as ex:
        raise RuntimeError('Wiring could not be generated') from ex 

    main = _compile_and_link(program.name, wiring, main_cpp)
    _copy_artifacts(main, node_inits, node_bodies, build_dir)

    if program.files != b'':
        zip_name = path.join(build_dir, "df_zip.zip")

        with open(zip_name, "wb") as zip_file:
            zip_file.write(program.files)

        df_zip = zipfile.ZipFile(zip_name, "r")

        if df_zip.testzip() is None:
            df_zip.extractall(build_dir)
        else:
            raise RuntimeError("Corrupted supporting files")
