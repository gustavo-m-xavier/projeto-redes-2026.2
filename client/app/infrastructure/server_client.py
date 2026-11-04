import json
import socket

from app.config.settings import ClientSettings

MAX_RESPONSE_BYTES = 1024 * 1024


class ServerControlClient:
    def __init__(self, settings: ClientSettings) -> None:
        self._settings = settings

    def send_command(self, action: str, port: int | None = None) -> dict:
        payload = {"token": self._settings.auth_token, "action": action}
        if port is not None:
            payload["port"] = port

        with socket.create_connection(
            (self._settings.server_host, self._settings.server_port),
            timeout=10,
        ) as connection:
            connection.sendall(json.dumps(payload).encode("utf-8") + b"\n")
            connection.shutdown(socket.SHUT_WR)
            response = connection.makefile("rb").readline(MAX_RESPONSE_BYTES + 1)

        if not response:
            raise ConnectionError("O servidor encerrou a conexão sem resposta.")
        if len(response) > MAX_RESPONSE_BYTES or not response.endswith(b"\n"):
            raise ValueError("Resposta inválida ou maior que o limite permitido.")
        return json.loads(response.decode("utf-8"))
