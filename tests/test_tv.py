import pytest

from tv import TvController, TvError, _magic_packet, wake_on_lan


def test_magic_packet_format():
    packet = _magic_packet("D8:E3:5E:34:DC:E6")
    assert len(packet) == 102
    assert packet[:6] == b"\xff" * 6
    assert packet[6:12] == bytes.fromhex("D8E35E34DCE6")


def test_magic_packet_invalid_mac():
    with pytest.raises(TvError):
        _magic_packet("D8E3")


def test_wake_on_lan_sends_magic_to_broadcast():
    sent = {}

    def sender(data):
        sent["data"] = data

    wake_on_lan("D8:E3:5E:34:DC:E6", sender=sender)
    assert sent["data"][:6] == b"\xff" * 6


class FakeWebOsClient:
    def __init__(self, connects=True):
        self.connects = connects
        self.power_off_called = False
        self.volume = None
        self.disconnected = False

    async def connect(self):
        return self.connects

    async def disconnect(self):
        self.disconnected = True

    async def power_off(self):
        self.power_off_called = True

    async def set_volume(self, volume):
        self.volume = volume
        return {"returnValue": True}


async def test_power_on_sends_wake_packet():
    woken = []
    tv = TvController(
        "192.168.18.172",
        "client-key",
        mac="D8:E3:5E:34:DC:E6",
        wake=lambda: woken.append(True),
    )
    result = await tv.set_power(True)
    assert woken == [True]
    assert result == {"on": True}


async def test_power_off_connects_and_powers_off():
    client = FakeWebOsClient()
    tv = TvController("192.168.18.172", "client-key", client_factory=lambda: client)
    result = await tv.set_power(False)
    assert client.power_off_called is True
    assert client.disconnected is True
    assert result == {"on": False}


async def test_volume_sets_and_validates_range():
    client = FakeWebOsClient()
    tv = TvController("192.168.18.172", "client-key", client_factory=lambda: client)
    assert await tv.set_volume(40) == {"volume": 40}
    assert client.volume == 40
    with pytest.raises(TvError):
        await tv.set_volume(101)


async def test_connect_failure_raises_tv_error():
    client = FakeWebOsClient(connects=False)
    tv = TvController("192.168.18.172", "client-key", client_factory=lambda: client)
    with pytest.raises(TvError):
        await tv.set_power(False)
