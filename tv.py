"""Controle local da TV LG via webOS (aiowebostv).

O firmware novo das TVs LG (webOS 22+) abandonou o canal ws://3000 e
exige wss://3001 com SSL nao verificado. aiopylgtv (lib antiga) nao
funciona com essa TV; aiowebostv faz o fallback ws->wss sozinho.
"""
import socket


class TvError(Exception):
    pass


class TvController:
    def __init__(self, host, client_key, mac=None, *, client_factory=None, wake=None):
        self._host = host
        self._client_key = client_key
        self._mac = mac
        self._client_factory = client_factory or (lambda: _new_client(host, client_key))
        self._wake = wake or (lambda: wake_on_lan(self._mac))

    async def set_power(self, on):
        if on:
            self._wake()
            return {"on": True}
        client = await self._connect()
        try:
            await client.power_off()
        finally:
            await client.disconnect()
        return {"on": False}

    async def set_volume(self, value):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise TvError("Volume deve estar entre 0 e 100.")
        client = await self._connect()
        try:
            await client.set_volume(value)
        finally:
            await client.disconnect()
        return {"volume": value}

    async def _connect(self):
        client = self._client_factory()
        if not await client.connect():
            raise TvError(
                "Nao foi possivel conectar na TV. Verifique se ela esta ligada "
                "e se o PC esta na mesma rede."
            )
        return client


def _new_client(host, client_key):
    from aiowebostv import WebOsClient

    return WebOsClient(host, client_key=client_key, connect_timeout=5)


def wake_on_lan(mac_address, sender=None):
    """Envia magic packet pra acordar a TV pela rede (UDP broadcast :9)."""
    magic = _magic_packet(mac_address)
    if sender is None:

        def sender(data):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(data, ("255.255.255.255", 9))

    sender(magic)


def _magic_packet(mac_address):
    mac = mac_address.replace(":", "").replace("-", "").replace(".", "")
    if len(mac) != 12:
        raise TvError(f"MAC invalido: '{mac_address}' (use formato AA:BB:CC:DD:EE:FF)")
    return bytes.fromhex("FF" * 6 + mac * 16)
