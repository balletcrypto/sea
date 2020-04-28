import logging
import os

from sea import exceptions, utils
from sea.config import Config, ConfigAttribute
from sea.datatypes import ConstantsObject, ImmutableDict


class Sea:
    """The BaseApp object implements grpc application

    :param root_path: the root path
    :param env: the env
    """

    _config_class = Config
    debug = ConfigAttribute("DEBUG")
    testing = ConfigAttribute("TESTING")

    default_config = ImmutableDict(
        {
            "DEBUG": False,
            "TESTING": False,
            "GRPC_HOST": "::",
            "GRPC_PORT": 50051,
            "GRPC_LOG_LEVEL": "INFO",
            "GRPC_REFLECTION": False,
            "GRPC_LOG_HANDLER": logging.StreamHandler(),
            "GRPC_LOG_FORMAT": "[%(asctime)s %(levelname)s in %(module)s] %(message)s",
            "PROMETHEUS_SCRAPE": False,
            "PROMETHEUS_PORT": 9091,
        }
    )

    def __init__(self, root_path):
        if not os.path.isabs(root_path):
            root_path = os.path.abspath(root_path)
        self.root_path = root_path
        self.name = os.path.basename(root_path)
        self.env = os.environ.get("SEA_ENV", "default")
        self.config = self.make_config()
        self._servicers = {}
        # self._extensions = {}

    def make_config(self):
        return self._config_class(self.root_path, self.default_config)

    @utils.cached_property
    def logger(self):
        logger = logging.getLogger("sea.app")
        if self.debug and logger.level == logging.NOTSET:
            logger.setLevel(logging.DEBUG)
        if not utils.logger_has_level_handler(logger):
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(h)
        return logger

    @utils.cached_property
    def servicers(self):
        rv = ConstantsObject(self._servicers)
        del self._servicers
        return rv

    @utils.cached_property
    def extensions(self):
        rv = ConstantsObject(self._extensions)
        del self._extensions
        return rv

    def register_servicer(self, servicers):
        """register servisers

        :param servicers: servicer list
        """
        for servicer in servicers:
            name = servicer.__name__
            if name in self._servicers:
                raise exceptions.ConfigException("servicer duplicated: {}".format(name))
            self._servicers[name] = servicer

        return self.servicers

    async def run(self):
        from sea.server import Server

        if len(self.servicers) == 0:
            raise RuntimeError("No servicers loaded")

        await Server(self).run()

    def register_extension(self, exts):
        """register extension

        :param exts: extension object
        """
        for ext in exts:
            ext.init_app(self)
            if ext.name in self._extensions:
                raise exceptions.ConfigException(f"extension duplicated: {ext.name}")
            self._extensions[ext.name] = ext
        return self.extensions
