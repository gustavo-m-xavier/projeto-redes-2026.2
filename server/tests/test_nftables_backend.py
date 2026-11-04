import subprocess
import unittest
from unittest.mock import patch

from app.infrastructure.firewall.nftables_backend import NftablesBackend


class NftablesBackendTests(unittest.TestCase):
    def test_lists_and_removes_only_rules_with_application_marker(self):
        backend = NftablesBackend()
        output = 'tcp dport 8080 comment "redes-monitor:8080" drop # handle 42\n'
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
            result = backend.unblock_port(8080)

        self.assertEqual(rules, [{"port": 8080, "status": "managed", "tool": "nft"}])
        self.assertEqual(result["status"], "unblocked")
        self.assertEqual(run.call_args.args[0][-2:], ["handle", "42"])


if __name__ == "__main__":
    unittest.main()
