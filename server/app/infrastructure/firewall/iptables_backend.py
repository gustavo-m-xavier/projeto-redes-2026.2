import re
import shlex
import subprocess


class IptablesBackend:
    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, capture_output=True, text=True, check=False)

    @staticmethod
    def _spec(port: int) -> list[str]:
        return [
            "-p",
            "tcp",
            "-m",
            "tcp",
            "--dport",
            str(port),
            "-m",
            "comment",
            "--comment",
            f"redes-monitor:{port}",
            "-j",
            "DROP",
        ]

    def block_port(self, port: int) -> dict:
        spec = self._spec(port)
        if self._run(["iptables", "-C", "INPUT", *spec]).returncode != 0:
            self._ensure_success(
                self._run(["iptables", "-I", "INPUT", *spec]),
                "Falha ao aplicar regra de bloqueio.",
            )
        return {"port": port, "status": "blocked", "tool": "iptables"}

    def unblock_port(self, port: int) -> dict:
        spec = self._spec(port)
        if self._run(["iptables", "-C", "INPUT", *spec]).returncode != 0:
            raise KeyError(f"Porta {port} não está sendo gerenciada pelo sistema.")
        self._ensure_success(
            self._run(["iptables", "-D", "INPUT", *spec]),
            "Falha ao remover regra de bloqueio.",
        )
        return {"port": port, "status": "unblocked", "tool": "iptables"}

    def list_rules(self) -> list[dict]:
        result = self._run(["iptables", "-S", "INPUT"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha ao consultar as regras iptables.")

        rules = []
        for line in result.stdout.splitlines():
            parts = shlex.split(line)
            marker = next((part for part in parts if re.fullmatch(r"redes-monitor:\d+", part)), None)
            if marker is None:
                continue
            port = int(marker.split(":", 1)[1])
            if self._is_managed_rule(parts, port):
                rules.append({"port": port, "status": "managed", "tool": "iptables"})
        return rules

    @staticmethod
    def _is_managed_rule(parts: list[str], port: int) -> bool:
        try:
            return (
                "-A" in parts
                and parts[parts.index("-A") + 1] == "INPUT"
                and parts[parts.index("-p") + 1] == "tcp"
                and parts[parts.index("--dport") + 1] == str(port)
                and parts[parts.index("-j") + 1] == "DROP"
            )
        except (ValueError, IndexError):
            return False

    @staticmethod
    def _ensure_success(result: subprocess.CompletedProcess, fallback: str) -> None:
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or fallback)
