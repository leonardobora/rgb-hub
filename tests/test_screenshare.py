import pytest

from screenshare import ScreenshareError, start_screenshare


class FakeTV:
    def __init__(self):
        self.power_on_called = False

    async def set_power(self, on):
        if on:
            self.power_on_called = True


async def test_start_screenshare_turns_tv_on_and_launches():
    tv = FakeTV()
    launched = []

    def launcher():
        launched.append(True)

    result = await start_screenshare(tv, launcher=launcher)
    assert tv.power_on_called is True
    assert launched == [True]
    assert result == {"status": "ok"}


async def test_start_screenshare_without_tv_still_launches():
    launched = []

    def launcher():
        launched.append(True)

    await start_screenshare(None, launcher=launcher)
    assert launched == [True]


def test_default_launcher_raises_when_startfile_missing(monkeypatch):
    monkeypatch.delattr("os.startfile", raising=False)

    async def run():
        from screenshare import _open_connected_devices

        with pytest.raises(ScreenshareError):
            _open_connected_devices()

    import asyncio

    asyncio.run(run())
