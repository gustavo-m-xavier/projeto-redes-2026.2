import hmac

from app.domain.ports import FirewallPort


class FirewallService:
    def __init__(self, firewall: FirewallPort, auth_token: str) -> None:
        self._firewall = firewall
        self._auth_token = auth_token

    def authorize(self, token: object) -> None:
        if (
            not self._auth_token
            or not isinstance(token, str)
            or not token
            or not hmac.compare_digest(token, self._auth_token)
        ):
            raise PermissionError("Token de autenticação inválido.")

    @staticmethod
    def validate_port(port: object) -> int:
        if isinstance(port, bool):
            raise ValueError("A porta deve ser um número inteiro entre 1 e 65535.")
        try:
            value = int(port)
        except (TypeError, ValueError) as exc:
            raise ValueError("A porta deve ser um número inteiro entre 1 e 65535.") from exc
        if value < 1 or value > 65535 or str(value) != str(port):
            raise ValueError("A porta deve ser um número inteiro entre 1 e 65535.")
        return value

    def block_port(self, port: object, token: str | None = None) -> dict:
        self.authorize(token)
        return self._firewall.block_port(self.validate_port(port))

    def unblock_port(self, port: object, token: str | None = None) -> dict:
        self.authorize(token)
        return self._firewall.unblock_port(self.validate_port(port))

    def list_rules(self) -> list[dict]:
        return self._firewall.list_rules()
