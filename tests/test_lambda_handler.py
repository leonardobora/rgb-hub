import httpx
import pytest

import lambda_handler


def _request(intent_name, slots=None):
    return {
        "request": {
            "type": "IntentRequest",
            "intent": {"name": intent_name, "slots": slots or {}},
        }
    }


def _slot(name, value):
    return {"name": name, "value": value}


def _text(response):
    return response["response"]["outputSpeech"]["text"]


class _FakeResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {}


def _fake_post(calls, *, status=200, body=None):
    class R(_FakeResponse):
        pass

    R.status_code = status
    if body is not None:
        R.headers = {"content-type": "application/json"}

        def json(self):
            return body

        R.json = json

    def post(url, json=None, timeout=None):
        calls.append((url, json))
        return R()

    return post


def test_launch_request_returns_greeting():
    resp = lambda_handler.handler({"request": {"type": "LaunchRequest"}}, None)
    assert "pronto" in _text(resp)


def test_scene_ok(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler.httpx, "post", _fake_post(calls))
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request("SceneIntent", {"cena": _slot("cena", "gaming")}), None
    )
    assert "gaming" in _text(resp)
    assert calls == [("https://hub.example/scene", {"name": "gaming"})]


def test_scene_invalid_returns_options(monkeypatch):
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request("SceneIntent", {"cena": _slot("cena", "copa")}), None
    )
    text = _text(resp)
    assert "gaming" in text and "foco" in text


def test_color_maps_name_to_hex(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler.httpx, "post", _fake_post(calls))
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request(
            "ColorIntent",
            {"luz": _slot("luz", "fita"), "cor": _slot("cor", "vermelho")},
        ),
        None,
    )
    assert calls[-1] == ("https://hub.example/color", {"name": "fita", "hex": "FF0000"})
    assert "fita" in _text(resp)


def test_color_unknown_light_returns_options(monkeypatch):
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request(
            "ColorIntent",
            {"luz": _slot("luz", "sala"), "cor": _slot("cor", "vermelho")},
        ),
        None,
    )
    assert "fita" in _text(resp)


def test_brightness_posts_pct(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler.httpx, "post", _fake_post(calls))
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request(
            "BrightnessIntent",
            {"luz": _slot("luz", "quarto"), "pct": _slot("pct", "50")},
        ),
        None,
    )
    assert calls[-1] == ("https://hub.example/brightness", {"name": "quarto", "pct": 50})
    assert "50" in _text(resp)


def test_sync_posts_mode(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler.httpx, "post", _fake_post(calls))
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request("SyncIntent", {"modo": _slot("modo", "audio")}), None
    )
    assert calls[-1] == ("https://hub.example/sync", {"mode": "audio"})
    assert "audio" in _text(resp)


def test_screenshare_posts(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler.httpx, "post", _fake_post(calls))
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(_request("ScreenshareIntent"), None)
    assert calls == [("https://hub.example/screenshare", {})]
    assert "Espelhamento" in _text(resp)


def test_hub_offline_says_offline(monkeypatch):
    def fail(url, json=None, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(lambda_handler.httpx, "post", fail)
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request("SceneIntent", {"cena": _slot("cena", "gaming")}), None
    )
    assert "offline" in _text(resp)


def test_hub_returns_error_body(monkeypatch):
    calls = []
    monkeypatch.setattr(
        lambda_handler.httpx,
        "post",
        _fake_post(calls, status=502, body={"error": "falha no tunel"}),
    )
    monkeypatch.setattr(lambda_handler, "HUB_URL", "https://hub.example")
    resp = lambda_handler.handler(
        _request("ColorIntent", {"luz": _slot("luz", "fita"), "cor": _slot("cor", "azul")}),
        None,
    )
    assert "falha no tunel" in _text(resp)
