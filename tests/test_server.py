from fastapi.testclient import TestClient

from lights import LightNotFound
from server import create_app


class FakeHub:
    def __init__(self):
        self.color = None
        self.brightness = None
        self.calls = []

    def list(self):
        return [{"name": "fita"}]

    def turn_on(self, name):
        self.calls.append(("turn_on", name))

    def set_color(self, name, hex_color):
        if name not in ("fita", "quarto"):
            raise LightNotFound(f"Luz '{name}' nao encontrada em devices.json/aliases.json")
        if not isinstance(hex_color, str) or len(hex_color) != 6:
            raise ValueError(f"Cor invalida: '{hex_color}' (use formato RRGGBB)")
        self.color = (name, hex_color)

    def set_brightness(self, name, pct):
        if name not in ("fita", "quarto"):
            raise LightNotFound(f"Luz '{name}' nao encontrada em devices.json/aliases.json")
        self.brightness = (name, pct)


class FakeSync:
    def __init__(self):
        self.mode = None

    def start(self, mode, light_names=None):
        if mode not in ("screen", "audio"):
            raise ValueError(f"Modo invalido: '{mode}'. Use 'screen' ou 'audio'.")
        self.mode = mode
        return {"mode": mode, "lights": ["fita"]}

    def stop(self):
        self.mode = None
        return {"mode": None}


class FakeTV:
    def __init__(self):
        self.calls = []

    async def set_power(self, on):
        self.calls.append(("power", on))
        return {"on": on}

    async def set_volume(self, value):
        self.calls.append(("volume", value))
        return {"volume": value}


def make_client(hub=None, sync=None, tv=None, launcher=None):
    app = create_app(
        hub=hub or FakeHub(),
        sync=sync or FakeSync(),
        tv=tv or FakeTV(),
        screenshare_launcher=launcher,
    )
    return TestClient(app)


def test_scene_ok():
    resp = make_client().post("/scene", json={"name": "gaming"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Cena gaming aplicada."


def test_scene_invalid_returns_error_json():
    resp = make_client().post("/scene", json={"name": "naoexiste"})
    assert resp.status_code == 404
    assert resp.json() == {"error": "Cena 'naoexiste' nao existe. Opcoes: gaming, foco, alerta"}


def test_color_ok():
    hub = FakeHub()
    resp = make_client(hub=hub).post("/color", json={"name": "fita", "hex": "FF00FF"})
    assert resp.status_code == 200
    assert hub.color == ("fita", "FF00FF")


def test_color_invalid_hex_returns_400():
    resp = make_client().post("/color", json={"name": "fita", "hex": "XYZ"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_color_unknown_light_returns_404():
    resp = make_client().post("/color", json={"name": "sala", "hex": "FFFFFF"})
    assert resp.status_code == 404
    assert "error" in resp.json()


def test_brightness_ok():
    hub = FakeHub()
    resp = make_client(hub=hub).post("/brightness", json={"name": "quarto", "pct": 60})
    assert resp.status_code == 200
    assert hub.brightness == ("quarto", 60)


def test_brightness_out_of_range_returns_400():
    resp = make_client().post("/brightness", json={"name": "fita", "pct": 150})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_sync_start_and_stop():
    sync = FakeSync()
    c = make_client(sync=sync)
    resp = c.post("/sync", json={"mode": "screen"})
    assert resp.status_code == 200
    assert sync.mode == "screen"
    resp = c.post("/sync", json={"mode": "off"})
    assert resp.status_code == 200
    assert sync.mode is None


def test_sync_invalid_mode_returns_400():
    resp = make_client().post("/sync", json={"mode": "lua"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_tv_on():
    tv = FakeTV()
    resp = make_client(tv=tv).post("/tv", json={"action": "on"})
    assert resp.status_code == 200
    assert tv.calls == [("power", True)]


def test_tv_volume_missing_value_returns_400():
    resp = make_client().post("/tv", json={"action": "volume"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_tv_invalid_action_returns_400():
    resp = make_client().post("/tv", json={"action": "mute"})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_screenshare_launches():
    launched = []

    def launcher():
        launched.append(True)

    resp = make_client(launcher=launcher).post("/screenshare")
    assert resp.status_code == 200
    assert launched == [True]
    assert resp.json()["message"].startswith("Espelhamento")
