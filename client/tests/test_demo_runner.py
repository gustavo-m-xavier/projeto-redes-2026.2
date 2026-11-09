import unittest
from unittest.mock import patch

from app.application.demo_runner import DemoRunner


class FakeServerClient:
    def __init__(self):
        self.actions = []

    def send_command(self, action, port=None):
        self.actions.append((action, port))
        return {"status": "ok"}


class FakeTrafficGenerator:
    def __init__(self, port_states):
        self.port_states = iter(port_states)

    def generate_http_traffic(self):
        return {"status_code": 200}

    def generate_dns_lookup(self):
        return {"status": "ok"}

    def is_tcp_port_open(self, _port, timeout=1.0):
        return next(self.port_states)


class DemoRunnerTests(unittest.TestCase):
    def test_checks_service_before_block_during_block_and_after_unblock(self):
        client = FakeServerClient()
        traffic = FakeTrafficGenerator([True, False, True])
        runner = DemoRunner(client, traffic, firewall_demo_port=8000, server_control_port=9000)

        with patch("app.application.demo_runner.time.sleep"):
            runner.run_once()

        self.assertEqual(
            client.actions,
            [("status", None), ("block", 8000), ("unblock", 8000)],
        )

    def test_does_not_apply_firewall_rule_when_target_service_is_unavailable(self):
        client = FakeServerClient()
        runner = DemoRunner(
            client,
            FakeTrafficGenerator([False]),
            firewall_demo_port=8000,
            server_control_port=9000,
        )

        with self.assertRaisesRegex(RuntimeError, "Não há serviço TCP acessível"):
            runner.run_once()

        self.assertEqual(client.actions, [("status", None)])

    def test_always_requests_unblock_when_block_verification_fails(self):
        client = FakeServerClient()
        traffic = FakeTrafficGenerator([True, True, True, True, True, True, True, True, True, True, True, True, True])
        runner = DemoRunner(client, traffic, firewall_demo_port=8000, server_control_port=9000)

        with patch("app.application.demo_runner.time.sleep"), patch(
            "app.application.demo_runner.time.monotonic",
            side_effect=[0, 4, 4],
        ):
            with self.assertRaisesRegex(RuntimeError, "continuou acessível"):
                runner.run_once()

        self.assertEqual(client.actions[-1], ("unblock", 8000))

    def test_rejects_control_port_as_demo_target(self):
        with self.assertRaisesRegex(ValueError, "porta do canal de controle"):
            DemoRunner(
                FakeServerClient(),
                FakeTrafficGenerator([]),
                firewall_demo_port=9000,
                server_control_port=9000,
            )


if __name__ == "__main__":
    unittest.main()
