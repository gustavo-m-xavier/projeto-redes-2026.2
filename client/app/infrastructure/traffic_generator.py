import socket

import requests

from app.config.settings import ClientSettings


class TrafficGenerator:
    def __init__(self, settings: ClientSettings) -> None:
        self._settings = settings

    def generate_http_traffic(self) -> dict:
        response = requests.get(
            f"http://{self._settings.server_host}:{self._settings.api_port}/health",
            timeout=10,
        )
        return {"status_code": response.status_code, "content": response.json()}

    @staticmethod
    def generate_dns_lookup() -> dict:
        socket.getaddrinfo("example.com", 80)
        return {"status": "ok", "domain": "example.com"}

    def is_tcp_port_open(self, port: int, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((self._settings.server_host, port), timeout=timeout):
                return True
        except OSError:
            return False
