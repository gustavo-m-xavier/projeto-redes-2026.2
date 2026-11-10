import subprocess
import unittest
from unittest.mock import patch

from app.infrastructure.firewall.iptables_backend import IptablesBackend
from app.infrastructure.firewall.firewall_manager import FirewallManager


class FirewallManagerTests(unittest.TestCase):
    def test_discovers_and_removes_only_application_rules_after_restart(self):
        manager = IptablesBackend()
        rule = "-A INPUT -p tcp -m tcp --dport 8080 -m comment --comment redes-monitor:8080 -j DROP"

        with patch.object(
            manager,
            "_run",
            side_effect=lambda command: subprocess.CompletedProcess(
                command,
                0,
                stdout=f"{rule}\n" if command[1] == "-S" else "",
                stderr="",
            ),
        ) as run:
            rules = manager.list_rules()
            result = manager.unblock_port(8080)

        self.assertEqual(rules, [{"port": 8080, "status": "managed", "tool": "iptables"}])
        self.assertEqual(result["status"], "unblocked")
        self.assertEqual(run.call_args.args[0][:3], ["iptables", "-D", "INPUT"])
        self.assertIn("redes-monitor:8080", run.call_args.args[0])

    def test_rejects_invalid_port_without_running_firewall_command(self):
        manager = FirewallManager(backend=IptablesBackend())

        with patch.object(IptablesBackend, "block_port") as run:
            with self.assertRaises(ValueError):
                manager.block_port(65536)

        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
