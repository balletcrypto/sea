import os

from sea import Sea
from sea.cli import JobException, jobm

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
    "protos",
    nargs="+",
    help="the proto files which will be compiled."
    'the paths are related to the path defined in "-I"',
)
def generate(proto_path, protos):
    from grpc_tools import protoc

    well_known_path = os.path.join(os.path.dirname(protoc.__file__), "_proto")
    print(well_known_path)

    proto_out = os.path.join(os.getcwd(), "protos")
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


@jobm.job("new", aliases=["n"], help="Create Sea Project")
@jobm.option("project", help="project name")
@jobm.option(
    "--skip-git", action="store_true", help="skip add git files and run git init"
)
@jobm.option("--skip-peewee", action="store_true", help="skip peewee")
@jobm.option("--skip-cache", action="store_true", help="skip cache")
@jobm.option("--skip-async-task", action="store_true", help="skip async_task")
@jobm.option("--skip-bus", action="store_true", help="skip bus")
@jobm.option("--skip-sentry", action="store_true", help="skip sentry")
def new(project, **extra):
    PACKAGE_DIR = os.path.dirname(__file__)
    TMPLPATH = os.path.join(PACKAGE_DIR, "template")
    IGNORED_FILES = {
        "git": ["gitignore"],
        "peewee": ["configs/default/peewee.py.tmpl", "app/models.py.tmpl"],
        "cache": ["configs/default/cache.py.tmpl"],
        "sentry": [],
        "async_task": ["configs/default/async_task.py.tmpl", "app/tasks.py.tmpl"],
        "bus": ["configs/default/bus.py.tmpl", "app/buses.py.tmpl"],
    }

    def _build_skip_files(extra):
        skipped = set()
        for ignore_key in IGNORED_FILES.keys():
            if extra[("skip_" + ignore_key)]:
                for f in IGNORED_FILES[ignore_key]:
                    skipped.add(os.path.join(TMPLPATH, f))
        return skipped

    def _gen_project(path, skip=set(), ctx={}):
        import shutil
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(TMPLPATH))
        for dirpath, dirnames, filenames in os.walk(TMPLPATH):
            for fn in filenames:
                src = os.path.join(dirpath, fn)
                if src not in skip:
                    relfn = os.path.relpath(src, TMPLPATH)
                    dst = os.path.join(path, relfn)
                    # create the parentdir if not exists
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    r, ext = os.path.splitext(dst)
                    if ext == ".tmpl":
                        with open(r, "w") as f:
                            tmpl = env.get_template(relfn)
                            f.write(tmpl.render(**ctx))
                    else:
                        shutil.copyfile(src, dst)

                    print("created: {}".format(dst))

    path = os.path.join(os.getcwd(), project)
    if os.path.exists(path):
        raise JobException("{} already exists".format(path))
    ctx = extra.copy()
    ctx["project"] = os.path.basename(path)
    _gen_project(path, skip=_build_skip_files(extra), ctx=ctx)
    return 0
