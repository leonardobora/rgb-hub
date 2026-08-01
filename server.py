"""API HTTP local (FastAPI) que expoe o rgb-hub pra Alexa (via tunel).

Endpoints:
  POST /scene         {name}
  POST /color         {name, hex}
  POST /brightness    {name, pct}
  POST /sync          {mode: screen|audio}  -- liga; {mode: off} desliga
  POST /screenshare
  POST /tv            {action: on|off|volume, value?}

Respostas de erro: JSON {"error": "<mensagem amigavel>"}.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

from lights import LightHub, LightNotFound
from scenes import apply_scene
from screenshare import ScreenshareError, start_screenshare
from sync_manager import SyncManager
from tv import TvController, TvError


class HubError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class SceneRequest(BaseModel):
    name: str


class ColorRequest(BaseModel):
    name: str
    hex: str


class BrightnessRequest(BaseModel):
    name: str
    pct: int


class SyncRequest(BaseModel):
    mode: str | None = None


class TvRequest(BaseModel):
    action: str
    value: int | None = None


def create_app(hub=None, sync=None, tv=None, screenshare_launcher=None):
    if hub is None:
        hub = LightHub()
    if sync is None:
        sync = SyncManager(hub)
    if tv is None:
        tv = TvController(
            os.getenv("TV_IP", ""),
            os.getenv("TV_CLIENT_KEY", ""),
            mac=os.getenv("TV_MAC", ""),
        )

    app = FastAPI(title="rgb-hub")

    @app.exception_handler(HubError)
    async def hub_error_handler(request: Request, exc: HubError):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    @app.post("/scene")
    def scene(req: SceneRequest):
        try:
            apply_scene(hub, req.name)
        except KeyError as exc:
            message = exc.args[0] if exc.args else str(exc)
            raise HubError(404, message) from exc
        return {"message": f"Cena {req.name} aplicada."}

    @app.post("/color")
    def color(req: ColorRequest):
        try:
            hub.set_color(req.name, req.hex)
        except LightNotFound as exc:
            raise HubError(404, str(exc)) from exc
        except ValueError as exc:
            raise HubError(400, str(exc)) from exc
        return {"message": f"Cor definida em {req.name}."}

    @app.post("/brightness")
    def brightness(req: BrightnessRequest):
        if not 0 <= req.pct <= 100:
            raise HubError(400, "Brilho deve estar entre 0 e 100.")
        try:
            hub.set_brightness(req.name, req.pct)
        except LightNotFound as exc:
            raise HubError(404, str(exc)) from exc
        return {"message": f"Brilho de {req.name} ajustado para {req.pct}%."}

    @app.post("/sync")
    def sync_endpoint(req: SyncRequest):
        try:
            if req.mode in (None, "off", "stop"):
                return {"message": "Sincronizacao desligada.", **sync.stop()}
            return {"message": "Sincronizacao ligada.", **sync.start(req.mode)}
        except ValueError as exc:
            raise HubError(400, str(exc)) from exc

    @app.post("/screenshare")
    async def screenshare():
        try:
            await start_screenshare(tv, launcher=screenshare_launcher)
        except (ScreenshareError, TvError) as exc:
            raise HubError(502, str(exc)) from exc
        return {
            "message": "Espelhamento iniciado. Clique na TV na janela que abriu.",
            "status": "ok",
        }

    @app.post("/tv")
    async def tv_endpoint(req: TvRequest):
        try:
            if req.action == "on":
                return await tv.set_power(True)
            if req.action == "off":
                return await tv.set_power(False)
            if req.action == "volume":
                if req.value is None:
                    raise HubError(400, "Informe 'value' (0-100) para volume.")
                return await tv.set_volume(req.value)
            raise HubError(400, f"Acao invalida: '{req.action}'. Use on|off|volume.")
        except TvError as exc:
            raise HubError(502, str(exc)) from exc

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("HUB_PORT", "8000")))
