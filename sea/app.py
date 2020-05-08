import logging

from sea import exceptions, utils
from sea.config import Config, ConfigAttribute
from sea.datatypes import ConstantsObject, ImmutableDict


class Sea:
    """The BaseApp object implements grpc application

    :param root_path: the root path
    """

    _config_class = Config
    debug = ConfigAttribute("DEBUG")
    testing = ConfigAttribute("TESTING")

    default_config = ImmutableDict(
        {
            "DEBUG": False,
            "TESTING": False,
            "LOG_LEVEL": "INFO",
            "LOG_HANDLER": logging.StreamHandler(),
            "LOG_FORMAT": "[%(asctime)s %(levelname)s in %(module)s] %(message)s",
            "GRPC_HOST": "::",
            "GRPC_PORT": 50051,
            "GRPC_REFLECTION": False,
            "PROMETHEUS_SCRAPE": False,
            "PROMETHEUS_PORT": 9091,
        }
    )

    def __init__(self, name):
        self.name = name
        self.config = self.make_config()

        self.servicers = ConstantsObject()
        self.extensions = ConstantsObject()

    def make_config(self):
        return self._config_class(self.default_config)

    @utils.cached_property
    def logger(self):
        logger = logging.getLogger("sea.app")
        if self.debug and logger.level == logging.DEBUG:
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
            if name in self.servicers:
                raise exceptions.ConfigException("servicer duplicated: {}".format(name))
            obj = servicer()
            obj.app = self
            self.servicers[name] = obj

    async def run(self):
        from sea.server import Server

        if len(self.servicers) == 0:
            raise RuntimeError("No servicers loaded")

        await Server(self).run()
