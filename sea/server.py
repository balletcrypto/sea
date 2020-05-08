from grpclib.reflection.service import ServerReflection
from grpclib.server import Server as GRPCServer
from grpclib.utils import graceful_exit


class Server:
    """sea server implements

    :param app: application instance
    """

    def __init__(self, app):
        self.app = app
        self.host = self.app.config["GRPC_HOST"]
        self.port = self.app.config["GRPC_PORT"]
        _servicers = [servicer for _, servicer in self.app.servicers.items()]
        if self.app.config["GRPC_REFLECTION"]:
            _servicers = ServerReflection.extend(_servicers)
        self.server = GRPCServer(_servicers)
        self._logger = self.app.logger

    async def run(self):
        # run prometheus client
        if self.app.config["PROMETHEUS_SCRAPE"]:
            try:
                from prometheus_client import start_http_server

                # start in a thread
                start_http_server(self.app.config["PROMETHEUS_PORT"])
            except ImportError:
                self._logger.logging.warning(
                    "Prometheus reporter not running, Please install prometheus_client."
                )

        # run grpc server, handle SIGINT and SIGTERM signals.
        with graceful_exit([self.server]):
            await self.server.start(self.host, self.port)
            # self._logger.info(f"Serving on [{self.host}]:{self.port}")
            await self.server.wait_closed()
            self._logger.info("Server closed")

        return True
