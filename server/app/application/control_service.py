from app.application.firewall_service import FirewallService
from app.application.monitoring_service import MonitoringService


class ControlService:
    def __init__(
        self,
        monitoring: MonitoringService,
        firewall: FirewallService,
    ) -> None:
        self._monitoring = monitoring
        self._firewall = firewall

    def execute(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            return {"status": "error", "message": "A solicitação JSON deve ser um objeto."}

        try:
            self._firewall.authorize(payload.get("token"))
            action = payload.get("action", "status")
            if action == "status":
                return {
                    **self._monitoring.status(self._firewall.list_rules()),
                    "status": "ok",
                }
            if action == "rules":
                return {"status": "ok", "result": self._firewall.list_rules()}
            if action == "block":
                return {
                    "status": "ok",
                    "result": self._firewall.block_port(payload.get("port"), payload.get("token")),
                }
            if action == "unblock":
                return {
                    "status": "ok",
                    "result": self._firewall.unblock_port(payload.get("port"), payload.get("token")),
                }
            return {"status": "error", "message": "Ação desconhecida."}
        except PermissionError as exc:
            return {"status": "error", "message": str(exc)}
        except (ValueError, KeyError, RuntimeError) as exc:
            return {"status": "error", "message": str(exc)}
