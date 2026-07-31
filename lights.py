"""Camada de controle local das luzes RGB via protocolo Tuya (lib tinytuya).

Pressupoe que 'devices.json' (gerado pelo wizard do tinytuya) e
'aliases.json' (nomes amigaveis -> device_id, opcional) existem na raiz
do projeto. NENHUM dos dois deve ir pro git: ambos guardam o local_key,
que da controle total do dispositivo pra quem tiver acesso a ele.
"""
import json
from pathlib import Path

import tinytuya

DEVICES_FILE = Path(__file__).parent / "devices.json"
ALIASES_FILE = Path(__file__).parent / "aliases.json"


class LightNotFound(KeyError):
    pass


class LightHub:
    def __init__(self, devices_file=DEVICES_FILE, aliases_file=ALIASES_FILE, version=3.3):
        self._devices_raw = _load_json(devices_file, required=True)
        self._aliases = _load_json(aliases_file, required=False) or {}
        self._version = version
        self._cache = {}

    def list(self):
        alias_by_id = {v: k for k, v in self._aliases.items()}
        return [
            {"name": alias_by_id.get(d["id"], d["id"]), "id": d["id"], "ip": d.get("ip", "?")}
            for d in self._devices_raw
        ]

    def turn_on(self, name):
        self._get_device(name).turn_on()

    def turn_off(self, name):
        self._get_device(name).turn_off()

    def set_color(self, name, hex_color):
        r, g, b = _hex_to_rgb(hex_color)
        self._get_device(name).set_colour(r, g, b)

    def set_brightness(self, name, percent):
        self._get_device(name).set_brightness_percentage(percent)

    def _resolve_id(self, name):
        if name in self._aliases:
            return self._aliases[name]
        if any(d["id"] == name for d in self._devices_raw):
            return name
        raise LightNotFound(f"Luz '{name}' nao encontrada em devices.json/aliases.json")

    def _get_device(self, name):
        dev_id = self._resolve_id(name)
        if dev_id not in self._cache:
            raw = next(d for d in self._devices_raw if d["id"] == dev_id)
            bulb = tinytuya.BulbDevice(dev_id, raw["ip"], raw["key"])
            bulb.set_version(self._version)
            self._cache[dev_id] = bulb
        return self._cache[dev_id]


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Cor invalida: '{hex_color}' (use formato RRGGBB)")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _load_json(path, required):
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"{path.name} nao encontrado. Rode 'python -m tinytuya wizard' primeiro "
                f"(veja o README) pra gerar esse arquivo."
            )
        return None
    return json.loads(path.read_text())
