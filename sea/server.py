import logging

from grpclib.reflection.service import ServerReflection
from grpclib.server import Server as GRPCServer
from grpclib.utils import graceful_exit


class Server:
    """sea server implements

    :param app: application instance
    """

    def __init__(self, app):
        self.app = app
        self.setup_logger()
        self.host = self.app.config["GRPC_HOST"]
        self.port = self.app.config["GRPC_PORT"]
        _servicers = [servicer for _, servicer in self.app.servicers.items()]
        if self.app.config["GRPC_REFLECTION"]:
            _servicers = ServerReflection.extend(_servicers)
        self.server = GRPCServer(_servicers)

    async def run(self):
        # run prometheus client
        if self.app.config["PROMETHEUS_SCRAPE"]:
            try:
                from prometheus_client import start_http_server

                # start in the thread
                start_http_server(self.app.config["PROMETHEUS_PORT"])
            except ImportError:
                logging.warning(
                    "Prometheus reporter not running, Please install prometheus_client."
                )

        # run grpc server, handle SIGINT and SIGTERM signals.
        with graceful_exit([self.server]):
            await self.server.start(self.host, self.port)
            logging.info(f"Serving on [{self.host}]:{self.port}")
            await self.server.wait_closed()

        return True

    def setup_logger(self):
        # TODO
        fmt = self.app.config["GRPC_LOG_FORMAT"]
        lvl = self.app.config["GRPC_LOG_LEVEL"]
        h = self.app.config["GRPC_LOG_HANDLER"]
        h.setFormatter(logging.Formatter(fmt))
        logger = logging.getLogger()
        logger.setLevel(lvl)
        logger.addHandler(h)
