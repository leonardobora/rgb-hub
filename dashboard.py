"""Dashboard HTTP com Server-Sent Events (SSE) pra mostrar
requisicoes e estado das luzes em tempo real.

Uso:
    python dashboard.py          # roda sozinho na porta 8001
    ou integra via include_router no server.py existente
"""
import asyncio
import json
import os
import time
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# log circular das ultimas 100 requisicoes
_request_log: deque = deque(maxlen=100)
_subscribers: list[asyncio.Queue] = []
_start_time = time.time()

# estado atual das luzes
_light_state: dict[str, dict] = {
    "fita": {"color": "000000", "brightness": 0},
    "quarto": {"color": "000000", "brightness": 0},
}
_current_mode = "off"


def create_dashboard_app(hub=None) -> FastAPI:
    app = FastAPI(title="rgb-hub dashboard")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html_path = os.path.join(static_dir, "dashboard.html")
        with open(html_path) as f:
            return HTMLResponse(f.read())

    @app.get("/dashboard/events")
    async def events(request: Request):
        queue: asyncio.Queue = asyncio.Queue()
        _subscribers.append(queue)

        async def generate():
            try:
                # envia estado atual ao conectar
                yield f"data: {json.dumps({'type': 'mode', 'mode': _current_mode})}\n\n"
                for name, state in _light_state.items():
                    yield f"data: {json.dumps({'type': 'light', 'name': name, 'hex': state['color'], 'brightness': state['brightness']})}\n\n"

                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        msg = await asyncio.wait_for(queue.get(), timeout=15)
                        yield f"data: {json.dumps(msg)}\n\n"
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            finally:
                if queue in _subscribers:
                    _subscribers.remove(queue)

        return StreamingResponse(generate(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/dashboard/state")
    async def state():
        return {"lights": _light_state, "mode": _current_mode, "uptime": time.time() - _start_time}

    @app.get("/dashboard/log")
    async def log():
        return {"entries": list(_request_log)}

    return app


def broadcast(msg: dict):
    """Envia mensagem pra todos os subscribers SSE."""
    for q in _subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass


def log_request(method: str, path: str, status: int, detail: str = ""):
    """Registra requisicao e notifica dashboard."""
    entry = {"type": "request", "method": method, "path": path, "status": status, "detail": detail}
    _request_log.append(entry)
    broadcast(entry)


def update_light_state(name: str, hex_color: str, brightness: int):
    """Atualiza estado de uma luz e notifica dashboard."""
    _light_state[name] = {"color": hex_color, "brightness": brightness}
    broadcast({"type": "light", "name": name, "hex": hex_color, "brightness": brightness})


def set_mode(mode: str):
    """Atualiza modo ativo e notifica dashboard."""
    global _current_mode
    _current_mode = mode
    broadcast({"type": "mode", "mode": mode})


if __name__ == "__main__":
    import uvicorn
    app = create_dashboard_app()
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("DASHBOARD_PORT", "8001")))
