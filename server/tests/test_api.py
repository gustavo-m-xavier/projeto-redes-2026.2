import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.application.firewall_service import FirewallService
from app.application.monitoring_service import MonitoringService, ServerInfo
from app.presentation.http.api import create_app


class FakeTelemetry:
    def snapshot(self):
        return {"pps": 0, "total_packets": 0}


class FakePacketCapture:
    last_error = None

    def get_packets(self, **_filters):
        return [{"protocol": "TCP", "length": 60}]


class FakeNetworkMonitor:
    def snapshot(self):
        return {"listeners": [], "connections": []}


class FakeFirewall:
    def __init__(self):
        self.blocked_ports = []

    def list_rules(self):
        return []

    def block_port(self, port):
        self.blocked_ports.append(port)
        return {"port": port, "status": "blocked"}

    def unblock_port(self, port):
        return {"port": port, "status": "unblocked"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.firewall = FakeFirewall()
        settings = SimpleNamespace(
            auth_token="test-token",
            server_host="0.0.0.0",
            server_port=9000,
            network_interface="lo",
        )
        monitoring = MonitoringService(
            ServerInfo(settings.server_host, settings.server_port, settings.network_interface),
            FakeTelemetry(),
            FakePacketCapture(),
            FakeNetworkMonitor(),
        )
        firewall = FirewallService(self.firewall, settings.auth_token)
        app = create_app(settings, monitoring, firewall)
        self.client = TestClient(app)

    def test_dashboard_api_exposes_live_data(self):
        response = self.client.get("/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["capture"]["interface"], "lo")
        self.assertEqual(self.client.get("/packets").json()["packets"][0]["protocol"], "TCP")

    def test_firewall_mutation_requires_authentication(self):
        response = self.client.post("/firewall/block/8080")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.firewall.blocked_ports, [])

    def test_firewall_mutation_accepts_valid_token(self):
        response = self.client.post(
            "/firewall/block/8080",
            headers={"X-Auth-Token": "test-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.firewall.blocked_ports, [8080])

    def test_websocket_stream_includes_packets_and_capture_state(self):
        with self.client.websocket_connect("/ws") as websocket:
            payload = websocket.receive_json()

        self.assertEqual(payload["packets"][0]["protocol"], "TCP")
        self.assertEqual(payload["capture"]["interface"], "lo")


if __name__ == "__main__":
    unittest.main()
