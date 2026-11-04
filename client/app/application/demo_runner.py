import logging
import time
from typing import Protocol

logger = logging.getLogger(__name__)


class ServerControlPort(Protocol):
    def send_command(self, action: str, port: int | None = None) -> dict: ...


class TrafficGeneratorPort(Protocol):
    def generate_http_traffic(self) -> dict: ...

    def generate_dns_lookup(self) -> dict: ...


class DemoRunner:
    def __init__(
        self,
        server_client: ServerControlPort,
        traffic_generator: TrafficGeneratorPort,
        firewall_demo_port: int = 8080,
    ) -> None:
        self._server_client = server_client
        self._traffic_generator = traffic_generator
        self._firewall_demo_port = firewall_demo_port

    def run_once(self) -> None:
        logger.info("Gerando tráfego HTTP: %s", self._traffic_generator.generate_http_traffic())
        logger.info("Executando consulta DNS: %s", self._traffic_generator.generate_dns_lookup())
        logger.info("Consultando o servidor: %s", self._server_client.send_command("status"))

        result = self._server_client.send_command("block", self._firewall_demo_port)
        logger.info("Resultado do bloqueio TCP/%d: %s", self._firewall_demo_port, result)
        if result.get("status") != "ok":
            logger.error("Bloqueio da porta de demonstração falhou; não será tentada a liberação.")
            return

        try:
            time.sleep(2)
        finally:
            logger.info(
                "Resultado da liberação TCP/%d: %s",
                self._firewall_demo_port,
                self._server_client.send_command("unblock", self._firewall_demo_port),
            )

    @staticmethod
    def keep_alive(interval_seconds: int = 30) -> None:
        while True:
            time.sleep(interval_seconds)
