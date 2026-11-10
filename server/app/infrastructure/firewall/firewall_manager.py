import platform
import shutil

from app.domain.ports import FirewallPort
from app.infrastructure.firewall.iptables_backend import IptablesBackend
from app.infrastructure.firewall.nftables_backend import NftablesBackend
from app.infrastructure.firewall.windows_firewall_backend import WindowsFirewallBackend


class FirewallManager:
    def __init__(self, backend: FirewallPort | None = None) -> None:
        self._backend = backend or self._select_backend()

    @staticmethod
    def _select_backend() -> FirewallPort:
        if platform.system() == "Windows":
            return WindowsFirewallBackend()
        if shutil.which("iptables"):
            return IptablesBackend()
        if shutil.which("nft"):
            return NftablesBackend()
        raise RuntimeError("Nenhum comando de firewall suportado foi encontrado (iptables/nft).")

    @staticmethod
    def _validate_port(port: int) -> int:
        value = int(port)
        if value < 1 or value > 65535:
            raise ValueError("Porta fora do intervalo válido.")
        return value

    def block_port(self, port: int) -> dict:
        return self._backend.block_port(self._validate_port(port))

    def unblock_port(self, port: int) -> dict:
        return self._backend.unblock_port(self._validate_port(port))

    def list_rules(self) -> list[dict]:
        return self._backend.list_rules()
