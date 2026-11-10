import unittest

from app.application.control_service import ControlService
from app.application.firewall_service import FirewallService
from app.application.monitoring_service import MonitoringService, ServerInfo


class FakeFirewall:
    def __init__(self):
        self.blocked = []

    def block_port(self, port):
        self.blocked.append(port)
        return {"port": port, "status": "blocked"}

    def unblock_port(self, port):
        self.blocked.remove(port)
        return {"port": port, "status": "unblocked"}

    def list_rules(self):
        return [{"port": port, "status": "managed"} for port in self.blocked]


class FakeTelemetry:
    def snapshot(self):
        return {"total_packets": 0}


class FakeCapture:
    last_error = None

    def get_packets(self, **_filters):
        return []


class FakeMonitor:
    def snapshot(self):
        return {"listeners": [], "connections": []}


class ControlServiceTests(unittest.TestCase):
    def setUp(self):
        firewall = FakeFirewall()
        monitoring = MonitoringService(
            ServerInfo("127.0.0.1", 9000, "lo"),
            FakeTelemetry(),
            FakeCapture(),
            FakeMonitor(),
        )
        self.firewall = firewall
        self.control = ControlService(monitoring, FirewallService(firewall, "secret"))

    def test_rejects_bad_token_and_malformed_payload(self):
        self.assertEqual(self.control.execute({"token": ["wrong"], "action": "block", "port": 80})["status"], "error")
        self.assertEqual(self.control.execute(["not", "an", "object"])["status"], "error")
        self.assertEqual(self.firewall.blocked, [])

    def test_allows_only_validated_firewall_operations(self):
        blocked = self.control.execute({"token": "secret", "action": "block", "port": "8080"})
        invalid = self.control.execute({"token": "secret", "action": "block", "port": True})

        self.assertEqual(blocked["status"], "ok")
        self.assertEqual(invalid["status"], "error")
        self.assertEqual(self.firewall.blocked, [8080])


if __name__ == "__main__":
    unittest.main()
