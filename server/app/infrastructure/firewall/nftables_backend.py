import re
import subprocess


class NftablesBackend:
    CHAIN = ("inet", "filter", "input")

    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def _rule_handle(self, port: int) -> str | None:
        result = self._run(["nft", "-a", "list", "chain", *self.CHAIN])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha ao consultar as regras nftables.")
        marker = f'redes-monitor:{port}'
        for line in result.stdout.splitlines():
            if marker in line:
                match = re.search(r"# handle (\d+)\s*$", line)
                if match:
                    return match.group(1)
        return None

    def block_port(self, port: int) -> dict:
        if self._rule_handle(port) is None:
            result = self._run(
                [
                    "nft",
                    "add",
                    "rule",
                    *self.CHAIN,
                    "tcp",
                    "dport",
                    str(port),
                    "comment",
                    f"redes-monitor:{port}",
                    "drop",
                ]
            )
            self._ensure_success(result, "Falha ao aplicar regra de bloqueio.")
        return {"port": port, "status": "blocked", "tool": "nft"}

    def unblock_port(self, port: int) -> dict:
        handle = self._rule_handle(port)
        if handle is None:
            raise KeyError(f"Porta {port} não está sendo gerenciada pelo sistema.")
        result = self._run(["nft", "delete", "rule", *self.CHAIN, "handle", handle])
        self._ensure_success(result, "Falha ao remover regra de bloqueio.")
        return {"port": port, "status": "unblocked", "tool": "nft"}

    def list_rules(self) -> list[dict]:
        result = self._run(["nft", "-a", "list", "chain", *self.CHAIN])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Falha ao consultar as regras nftables.")
        rules = []
        for line in result.stdout.splitlines():
            match = re.search(r'tcp dport (\d+).*comment "redes-monitor:\1".*drop.*# handle \d+\s*$', line)
            if match:
                rules.append({"port": int(match.group(1)), "status": "managed", "tool": "nft"})
        return rules

    @staticmethod
    def _ensure_success(result: subprocess.CompletedProcess, fallback: str) -> None:
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or fallback)
