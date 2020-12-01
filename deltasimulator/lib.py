import asyncio
from os import path
from deltasimulator.build_tools import BuildArtifact, write
from deltasimulator.build_tools.environments import (PythonatorEnv,
                                                     VerilatorEnv,
                                                     WiringEnv,
                                                     CPPEnv,
                                                     HostEnv)

def build_program(program):
    """ This function creates wiring and object files for the full build """
    node_headers = []
    node_bodies = []
    node_modules = []
    node_objects = []
    node_inits = []
    verilated_o = None
    for node in program.nodes:
        if node.body != -1:
            # If node.body is -1 then it is a template node
            # and cannot be pythonated
            which_body = program.bodies[node.body].which()

            if which_body in ['python', 'interactive'] :
                with PythonatorEnv(program.bodies) as env:
                    build_artifacts = env.pythonate(node)
                    node_headers.append(build_artifacts["h"])
                    if "py" in build_artifacts:
                        node_bodies.append(build_artifacts["py"])
                    node_modules.append(build_artifacts["cpp"])
                    node_objects.append(build_artifacts["o"])

            elif which_body == 'migen':
                # This part is adopted from initial-example:
                top_v = BuildArtifact(name=f"{node.name}.v",
                                      data=program.bodies[node.body].migen.verilog.encode("utf8"))

                with VerilatorEnv() as env:
                    build_artifacts = env.verilate(top_v)

                node_headers.append(build_artifacts["h"])
                node_modules.append(build_artifacts["cpp"])
                node_objects.append(build_artifacts["ALL.a"])
                node_inits += build_artifacts["init"]
                if not verilated_o:
                    verilated_o = build_artifacts["verilated.o"]

    with WiringEnv(program.nodes,
                   program.bodies,
                   node_headers,
                   node_objects,
                   verilated_o,
                   program.name) as env:
        wiring = env.wiring(program.graph)

    return node_bodies, node_inits, wiring

async def _wait_for_build(wiring):
    """ This function will wait for the artifacts to be built """
    for comp in wiring:
        _ = await asyncio.wait_for(wiring[comp].data, timeout=None)

def _copy_artifacts(main, inits, node_bodies, destination):
    """ This function copies all the built artifacts to a given destination """
    for init in inits:
        with open(path.join(destination, init.name), "wb") as f:
            write(init, f)

    for body in node_bodies:
        with open(path.join(destination, body.name), "wb") as f:
            write(body, f)

    with open(path.join(destination, "main"), "wb") as f:
        write(main, f)


def _compile_and_link(program_name, wiring, main_cpp):
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


def full_build(program, main_cpp, build_dir):
    """ This function compiles a program in a specified directory. 
    A top level wrapper need to be provided. """
    node_bodies, node_inits, wiring = build_program(program)
    main = _compile_and_link(program.name, wiring, main_cpp)
    _copy_artifacts(main, node_inits, node_bodies, build_dir)



