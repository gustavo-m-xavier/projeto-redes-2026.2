import json
import logging
import socketserver

from app.application.control_service import ControlService

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 1024 * 1024


class _ThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    control_service: ControlService


class _ControlRequestHandler(socketserver.StreamRequestHandler):
    def setup(self) -> None:
        super().setup()
        self.request.settimeout(10)

    def handle(self) -> None:
        request = self.rfile.readline(MAX_REQUEST_BYTES + 1)
        if len(request) > MAX_REQUEST_BYTES or not request.endswith(b"\n"):
            self._send({"status": "error", "message": "A solicitação deve ser uma linha JSON de até 4096 bytes."})
            return

        try:
            payload = json.loads(request.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send({"status": "error", "message": "A solicitação deve conter JSON UTF-8 válido."})
            return

        response = self.server.control_service.execute(payload)
        self._send(response)

    def _send(self, payload: dict) -> None:
        response = json.dumps(payload).encode("utf-8") + b"\n"
        if len(response) > MAX_RESPONSE_BYTES:
            logger.error("Resposta do controle TCP excedeu o limite de %d bytes", MAX_RESPONSE_BYTES)
            response = b'{"status":"error","message":"Resposta excede o limite permitido."}\n'
        self.wfile.write(response)


class ControlTCPServer:
    def __init__(self, host: str, port: int, control_service: ControlService) -> None:
        self._server = _ThreadingTCPServer(
            (host, port),
            _ControlRequestHandler,
            bind_and_activate=True,
        )
        self._server.control_service = control_service

    def serve_forever(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
