import os
import sys

from sea.app import Sea
from sea.local import Proxy
from sea.server import Server
from sea.utils import import_string

__all__ = ("Sea", "create_app", "current_app", "Server")


__version__ = "2.2.0"
_app = None


def create_app(root_path=None):
    global _app
    if _app is not None:
        return _app

    if root_path is None:
        root_path = os.getcwd()
    sys.path.append(root_path)
    sys.path.append(os.path.join(root_path, "protos"))

    env = os.environ.get("SEA_ENV", "development")
    config = import_string("configs.{}".format(env))

    try:
        app_class = import_string("app:App")
    except ImportError:
        app_class = Sea

    _app = app_class(root_path, env=env)
    _app.config.from_object(config)

    try:
        _app.load_middlewares()
    except ImportError as e:
        _app.logger.warning(e)

    try:
        _app.load_extensions_in_module(import_string("app.extensions"))
    except ImportError as e:
        _app.logger.warning(e)

    try:
        _app.load_servicers_in_module(import_string("app.servicers"))
    except ImportError as e:
        _app.logger.warning(e)

    _app.ready()

    return _app


current_app = Proxy(lambda: _app)
