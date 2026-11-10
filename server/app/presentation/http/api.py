import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from app.application.firewall_service import FirewallService
from app.application.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)


def create_app(
    settings,
    monitoring: MonitoringService,
    firewall: FirewallService,
) -> FastAPI:
    app = FastAPI(title="Rede Monitor")

    def token_from_request(request: Request) -> str | None:
        token = request.headers.get("X-Auth-Token")
        if token is None:
            authorization = request.headers.get("Authorization", "")
            token = authorization.removeprefix("Bearer ")
        return token

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": "server"}

    @app.get("/status")
    async def status() -> dict:
        return monitoring.status(firewall.list_rules())

    @app.get("/packets")
    async def packets(
        ip: str | None = Query(default=None),
        port: int | None = Query(default=None),
        protocol: str | None = Query(default=None),
    ) -> dict:
        return {"packets": monitoring.packets(ip=ip, port=port, protocol=protocol)}

    @app.get("/connections")
    async def connections() -> dict:
        return monitoring.connections()

    @app.get("/firewall/rules")
    async def firewall_rules() -> dict:
        return {"rules": firewall.list_rules()}

    @app.post("/firewall/block/{port}")
    async def firewall_block(port: int, request: Request) -> dict:
        try:
            return {"result": firewall.block_port(port, token_from_request(request))}
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/firewall/unblock/{port}")
    async def firewall_unblock(port: int, request: Request) -> dict:
        try:
            return {"result": firewall.unblock_port(port, token_from_request(request))}
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(monitoring.live_snapshot(firewall.list_rules()))
                await asyncio.sleep(1.5)
        except WebSocketDisconnect:
            logger.debug("Cliente WebSocket desconectado")

    static_dir = Path(__file__).parents[2] / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="dashboard")

    return app
