import logging
import socket
import threading

import psutil

from app.domain.ports import NetworkMonitorPort

logger = logging.getLogger(__name__)


class PsutilNetworkMonitor(NetworkMonitorPort):
    def __init__(self, interval_seconds: float = 2.0):
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None
        self._last_snapshot = {"listeners": [], "connections": []}
        self._snapshot_lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = self._read_snapshot()
            except psutil.Error:
                logger.exception("Falha ao consultar as conexões do sistema")
            else:
                with self._snapshot_lock:
                    self._last_snapshot = snapshot
            self._stop_event.wait(self.interval_seconds)

    def snapshot(self) -> dict:
        with self._snapshot_lock:
            return {
                "listeners": list(self._last_snapshot["listeners"]),
                "connections": list(self._last_snapshot["connections"]),
            }

    @staticmethod
    def _read_snapshot() -> dict:
        connections = []
        for connection in psutil.net_connections(kind="inet"):
            local_address = connection.laddr.ip if connection.laddr else "-"
            local_port = connection.laddr.port if connection.laddr else None
            remote_address = connection.raddr.ip if connection.raddr else "-"
            remote_port = connection.raddr.port if connection.raddr else None
            if connection.type == socket.SOCK_STREAM:
                protocol = "TCP"
            elif connection.type == socket.SOCK_DGRAM:
                protocol = "UDP"
            else:
                protocol = "UNKNOWN"
            connections.append(
                {
                    "fd": connection.fd,
                    "family": str(connection.family),
                    "status": str(connection.status),
                    "local_address": local_address,
                    "local_port": local_port,
                    "remote_address": remote_address,
                    "remote_port": remote_port,
                    "protocol": protocol,
                }
            )

        listeners = [item for item in connections if str(item["status"]).upper() == "LISTEN"]

        return {"listeners": listeners, "connections": connections}
