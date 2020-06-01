import contextvars
import time
from typing import Optional, cast

from grpclib.events import RecvRequest, SendTrailingMetadata, listen
from grpclib.reflection.service import ServerReflection
from grpclib.server import Server as GRPCServer
from grpclib.utils import graceful_exit

XRequestId = Optional[str]
request_id: contextvars.ContextVar[XRequestId] = contextvars.ContextVar("x-request-id")
start_time: contextvars.ContextVar[float] = contextvars.ContextVar("start_time")


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

    async def on_recv_request(self, event: RecvRequest) -> None:
        r_id = cast(XRequestId, event.metadata.get("x-request-id"))
        request_id.set(r_id)
        start_time.set(time.perf_counter())
        self._logger.info(
            "req_id: {}, recv method call {}".format(r_id, event.method_name)
        )

    async def on_send_trailing_metadata(self, event: SendTrailingMetadata) -> None:
        self._logger.info(
            "req_id: {}, Execution time {:.2f} ms".format(
                request_id.get(), (time.perf_counter() - float(start_time.get())) * 1000
            )
        )

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

        # https://grpclib.readthedocs.io/en/latest/overview.html#grpclib
        listen(self.server, RecvRequest, self.on_recv_request)
        listen(self.server, SendTrailingMetadata, self.on_send_trailing_metadata)

        # run grpc server, handle SIGINT and SIGTERM signals.
        with graceful_exit([self.server]):
            await self.server.start(self.host, self.port)
            self._logger.info(f"Serving on [{self.host}]:{self.port}")
            await self.server.wait_closed()
            for func in self.app.on_shutdown:
                await func()

            self._logger.info("Server shutdown")

        return True
