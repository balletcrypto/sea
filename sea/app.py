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

        self.servicers = ConstantsObject()
        self.extensions = ConstantsObject()

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

    def register_servicer(self, servicers):
        """register servisers

        :param servicers: servicer list
        """
        for servicer in servicers:
            name = servicer.__name__
            if name in self._servicers:
                raise exceptions.ConfigException("servicer duplicated: {}".format(name))
            self.servicers[name] = servicer

    async def run(self):
        from sea.server import Server

        if len(self.servicers) == 0:
            raise RuntimeError("No servicers loaded")

        await Server(self).run()
