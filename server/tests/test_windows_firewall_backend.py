import subprocess
import unittest
from unittest.mock import patch

from app.infrastructure.firewall.firewall_manager import FirewallManager
from app.infrastructure.firewall.windows_firewall_backend import WindowsFirewallBackend


class WindowsFirewallBackendTests(unittest.TestCase):
    def test_creates_a_tcp_inbound_block_rule(self):
        backend = WindowsFirewallBackend()
        with patch.object(
            backend,
            "_run",
            return_value=subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ) as run:
            result = backend.block_port(80)

        script = run.call_args.args[0]
        self.assertIn("New-NetFirewallRule", script)
        self.assertIn("-Direction Inbound -Action Block -Protocol TCP -LocalPort 80", script)
        self.assertEqual(result["status"], "blocked")

    def test_lists_managed_rules_and_removes_only_the_requested_port(self):
        backend = WindowsFirewallBackend()
        output = '["RedesMonitor-TCP-In-80","unrelated-rule","RedesMonitor-TCP-In-443"]'
        with patch.object(
            backend,
            "_run",
            side_effect=[
                subprocess.CompletedProcess([], 0, stdout=output, stderr=""),
                subprocess.CompletedProcess([], 0, stdout=output, stderr=""),
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            ],
        ) as run:
            rules = backend.list_rules()
            result = backend.unblock_port(80)

        self.assertEqual([rule["port"] for rule in rules], [80, 443])
        self.assertIn("Get-NetFirewallPortFilter", run.call_args_list[0].args[0])
        self.assertEqual(result["status"], "unblocked")
        self.assertIn("Get-NetFirewallRule -Name 'RedesMonitor-TCP-In-80'", run.call_args.args[0])
        self.assertIn("Remove-NetFirewallRule", run.call_args.args[0])

    def test_manager_selects_windows_backend(self):
        with patch("app.infrastructure.firewall.firewall_manager.platform.system", return_value="Windows"):
            manager = FirewallManager()

        self.assertIsInstance(manager._backend, WindowsFirewallBackend)

    def test_reports_powershell_errors(self):
        backend = WindowsFirewallBackend()
        with patch.object(
            backend,
            "_run",
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="Access is denied."),
        ):
            with self.assertRaisesRegex(RuntimeError, "Access is denied"):
                backend.block_port(80)

    def test_lists_no_rules_when_powershell_returns_null(self):
        backend = WindowsFirewallBackend()
        with patch.object(
            backend,
            "_run",
            return_value=subprocess.CompletedProcess([], 0, stdout="null", stderr=""),
        ):
            self.assertEqual(backend.list_rules(), [])


if __name__ == "__main__":
    unittest.main()
