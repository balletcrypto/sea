import os

from sea import Sea
from sea.cli import jobm

# from sea import Server
# TODO console_scripts can not run async function
# @jobm.job("server", aliases=["s"], help="Run Server")
# def server():
#     s = Server(current_app)
#     s.run()
#     return 0


@jobm.job("shell", aliases=["c"], help="Run Console in shell")
def console():
    banner = """
        [Sea Console]:
        the following vars are included:
        `app` (the Sea(__name__))
        """
    ctx = {"app": Sea(__name__)}
    try:
        from IPython import embed

        h, kwargs = embed, dict(banner1=banner, user_ns=ctx, colors="neutral")
    except ImportError:
        import code

        h, kwargs = code.interact, dict(banner=banner, local=ctx)
    h(**kwargs)
    return 0


@jobm.job("generate", aliases=["g"], help="Generate RPC")
@jobm.option(
    "-I",
    "--proto_path",
    required=True,
    action="append",
    help="the dir in which we'll search the proto files",
)
@jobm.option(
    "-O",
    "--proto_out_path",
    required=True,
    help="the dir in which we'll generate the output proto files",
)
@jobm.option(
    "protos",
    nargs="+",
    help="the proto files which will be compiled."
    'the paths are related to the path defined in "-I"',
)
def generate(proto_path, proto_out_path, protos):
    from grpc_tools import protoc

    well_known_path = os.path.join(os.path.dirname(protoc.__file__), "_proto")

    proto_out = os.path.join(os.getcwd(), proto_out_path)

    proto_path.append(well_known_path)
    proto_path_args = []
    for protop in proto_path:
        proto_path_args += ["--proto_path", protop]
    cmd = [
        "grpc_tools.protoc",
        *proto_path_args,
        "--python_out",
        proto_out,
        "--grpc_python_out",
        proto_out,
        "--python_grpc_out",
        proto_out,
        *protos,
    ]
    return protoc.main(cmd)
