import logging
import time
from typing import Protocol

logger = logging.getLogger(__name__)


class ServerControlPort(Protocol):
    def send_command(self, action: str, port: int | None = None) -> dict: ...


class TrafficGeneratorPort(Protocol):
    def generate_http_traffic(self) -> dict: ...

    def generate_dns_lookup(self) -> dict: ...

    def is_tcp_port_open(self, port: int, timeout: float = 1.0) -> bool: ...


class DemoRunner:
    def __init__(
        self,
        server_client: ServerControlPort,
        traffic_generator: TrafficGeneratorPort,
        firewall_demo_port: int = 8000,
        server_control_port: int | None = None,
    ) -> None:
        self._server_client = server_client
        self._traffic_generator = traffic_generator
        self._firewall_demo_port = firewall_demo_port
        if not 1 <= firewall_demo_port <= 65535:
            raise ValueError("A porta de demonstração deve estar entre 1 e 65535.")
        if server_control_port is not None and firewall_demo_port == server_control_port:
            raise ValueError("A porta de demonstração não pode ser a porta do canal de controle.")

    def run_once(self) -> None:
        logger.info("Gerando tráfego HTTP: %s", self._traffic_generator.generate_http_traffic())
        logger.info("Executando consulta DNS: %s", self._traffic_generator.generate_dns_lookup())
        status = self._server_client.send_command("status")
        logger.info("Consultando o servidor: %s", status)
        if status.get("status") != "ok":
            raise RuntimeError("Não foi possível confirmar o estado do servidor de controle.")

        if not self._traffic_generator.is_tcp_port_open(self._firewall_demo_port):
            raise RuntimeError(
                f"Não há serviço TCP acessível na porta {self._firewall_demo_port} da máquina B."
            )

        result = self._server_client.send_command("block", self._firewall_demo_port)
        logger.info("Resultado do bloqueio TCP/%d: %s", self._firewall_demo_port, result)
        if result.get("status") != "ok":
            raise RuntimeError("O servidor não conseguiu aplicar a regra de bloqueio.")

        try:
            if not self._wait_for_port_state(False):
                raise RuntimeError(
                    f"A porta TCP/{self._firewall_demo_port} continuou acessível após o bloqueio."
                )
            logger.info("Comprovado: novas conexões TCP/%d foram bloqueadas.", self._firewall_demo_port)
            time.sleep(2)
        finally:
            result = self._server_client.send_command("unblock", self._firewall_demo_port)
            logger.info("Resultado da liberação TCP/%d: %s", self._firewall_demo_port, result)
            if result.get("status") != "ok":
                raise RuntimeError("O servidor não conseguiu remover a regra de bloqueio.")

        if not self._wait_for_port_state(True):
            raise RuntimeError(
                f"A porta TCP/{self._firewall_demo_port} não voltou a aceitar conexões após a liberação."
            )
        logger.info("Comprovado: novas conexões TCP/%d foram restauradas.", self._firewall_demo_port)

    def _wait_for_port_state(self, expected_open: bool, timeout_seconds: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while True:
            if self._traffic_generator.is_tcp_port_open(self._firewall_demo_port) is expected_open:
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(0.25, remaining))

    @staticmethod
    def keep_alive(interval_seconds: int = 30) -> None:
        while True:
            time.sleep(interval_seconds)
