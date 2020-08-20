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
            "LOG_FORMAT": "%(asctime)s:%(filename)s:%(lineno)d %(levelname)s/%(processName)s %(message)s",
            "GRPC_HOST": "0.0.0.0",
            "GRPC_PORT": 50051,
            "GRPC_REFLECTION": False,
            "HEALTH_CHECKING": False,
            "PROMETHEUS_SCRAPE": False,
            "PROMETHEUS_PORT": 9091,
        }
    )

    def __init__(self, name):
        self.name = name
        self.config = self.make_config()

        self.servicers = ConstantsObject()
        self.extensions = ConstantsObject()
        self._on_shutdown = []

    @property
    def on_shutdown(self):
        return self._on_shutdown

    def make_config(self):
        return self._config_class(self.default_config)

    @utils.cached_property
    def logger(self):
        logger = logging.getLogger("sea.app")
        logger.propagate = False  # disable root logger

        level = self.config["LOG_LEVEL"]
        logger.setLevel(level)

        h = logging.StreamHandler()
        h.setLevel(level)
        h.setFormatter(logging.Formatter(self.config["LOG_FORMAT"]))
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
            svc = servicer()
            if hasattr(svc, "inject_app"):
                svc.inject_app(self)

            self.servicers[name] = svc

    async def run(self):
        from sea.server import Server

        if len(self.servicers) == 0:
            raise RuntimeError("No servicers loaded")

        await Server(self).run()
