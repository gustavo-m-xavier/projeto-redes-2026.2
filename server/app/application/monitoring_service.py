from dataclasses import dataclass

from app.domain.ports import NetworkMonitorPort, PacketCapturePort, TelemetryPort


@dataclass(frozen=True)
class ServerInfo:
    host: str
    control_port: int
    network_interface: str


class MonitoringService:
    def __init__(
        self,
        server_info: ServerInfo,
        telemetry: TelemetryPort,
        packet_capture: PacketCapturePort,
        network_monitor: NetworkMonitorPort,
    ) -> None:
        self._server_info = server_info
        self._telemetry = telemetry
        self._packet_capture = packet_capture
        self._network_monitor = network_monitor

    def status(self, firewall_rules: list[dict] | None = None) -> dict:
        return {
            "server": {
                "host": self._server_info.host,
                "port": self._server_info.control_port,
            },
            "telemetry": self._telemetry.snapshot(),
            "ports": self._network_monitor.snapshot(),
            "firewall": firewall_rules or [],
            "capture": self.capture_status(),
        }

    def capture_status(self) -> dict:
        return {
            "interface": self._server_info.network_interface,
            "error": self._packet_capture.last_error,
        }

    def packets(
        self,
        ip: str | None = None,
        port: int | None = None,
        protocol: str | None = None,
    ) -> list[dict]:
        return self._packet_capture.get_packets(ip=ip, port=port, protocol=protocol)

    def connections(self) -> dict:
        return self._network_monitor.snapshot()

    def live_snapshot(self, firewall_rules: list[dict]) -> dict:
        return {
            "telemetry": self._telemetry.snapshot(),
            "connections": self._network_monitor.snapshot(),
            "firewall": firewall_rules,
            "packets": self._packet_capture.get_packets(),
            "capture": self.capture_status(),
        }
