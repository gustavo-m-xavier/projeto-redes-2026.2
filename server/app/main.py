import logging
import threading

import uvicorn

from app.application.control_service import ControlService
from app.application.firewall_service import FirewallService
from app.application.monitoring_service import MonitoringService, ServerInfo
from app.config import settings
from app.infrastructure.capture.scapy_packet_analyzer import ScapyPacketAnalyzer
from app.infrastructure.capture.scapy_packet_capture import ScapyPacketCapture
from app.infrastructure.firewall.firewall_manager import FirewallManager
from app.infrastructure.monitoring.psutil_network_monitor import PsutilNetworkMonitor
from app.infrastructure.telemetry.in_memory_telemetry import InMemoryTelemetry
from app.presentation.http.api import create_app
from app.presentation.tcp.control_server import ControlTCPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

telemetry = InMemoryTelemetry()
packet_capture = ScapyPacketCapture(
    network_interface=settings.network_interface,
    analyzer=ScapyPacketAnalyzer(),
    telemetry=telemetry,
)
network_monitor = PsutilNetworkMonitor()
firewall_backend = FirewallManager()
monitoring_service = MonitoringService(
    ServerInfo(settings.server_host, settings.server_port, settings.network_interface),
    telemetry,
    packet_capture,
    network_monitor,
)
firewall_service = FirewallService(firewall_backend, settings.auth_token)
control_service = ControlService(monitoring_service, firewall_service)
control_server = ControlTCPServer(settings.server_host, settings.server_port, control_service)
app = create_app(settings, monitoring_service, firewall_service)


if __name__ == "__main__":
    packet_capture.start()
    network_monitor.start()
    control_thread = threading.Thread(target=control_server.serve_forever, daemon=True)
    control_thread.start()
    try:
        uvicorn.run(app, host=settings.server_host, port=settings.api_port)
    finally:
        control_server.shutdown()
        packet_capture.stop()
        network_monitor.stop()
