import time

import pytest

from sync_manager import SyncManager


class FakeHub:
    def __init__(self):
        self.sent = []
        self.names = ["fita", "quarto"]

    def list(self):
        return [{"name": n} for n in self.names]

    def set_color(self, name, hex_color):
        self.sent.append((name, hex_color))


def fake_source():
    while True:
        yield (10, 20, 30)


def test_start_screen_runs_and_stops(monkeypatch):
    hub = FakeHub()
    mgr = SyncManager(hub)
    monkeypatch.setattr("screen_source.screen_colors", lambda **kw: fake_source())
    assert mgr.start("screen")["mode"] == "screen"
    time.sleep(0.4)
    assert mgr.mode == "screen"
    assert mgr.is_running()
    assert len(hub.sent) > 0
    mgr.stop()
    assert mgr.mode is None
    assert not mgr.is_running()


def test_start_switches_mode(monkeypatch):
    hub = FakeHub()
    mgr = SyncManager(hub)
    monkeypatch.setattr("screen_source.screen_colors", lambda **kw: fake_source())
    mgr.start("screen")
    time.sleep(0.1)
    assert mgr.start("audio")["mode"] == "audio"
    assert mgr.mode == "audio"
    mgr.stop()


def test_start_invalid_mode_raises():
    mgr = SyncManager(FakeHub())
    with pytest.raises(ValueError):
        mgr.start("tela")


def test_stop_when_not_running_returns_none():
    mgr = SyncManager(FakeHub())
    assert mgr.stop() == {"mode": None}
