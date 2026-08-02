"""Paletas de cores pre-definidas mapeando bandas de frequencia (grave/
medio/agudo) pra RGB. Cada tema recebe valores das bandas em 0..255
(escala fixa com gain) e retorna (r, g, b) em 0..255.
"""
from dataclasses import dataclass
from typing import Callable


ThemeFunc = Callable[[int, int, int], tuple[int, int, int]]


@dataclass
class Theme:
    name: str
    apply: ThemeFunc


def _clamp(value):
    return int(max(0, min(255, value)))


def _rainbow(bass, mid, treble):
    return bass, mid, treble


def _fire(bass, mid, treble):
    r = bass * 0.7 + mid * 0.3
    g = mid * 0.6 + treble * 0.4
    b = treble * 0.3
    return _clamp(r), _clamp(g), _clamp(b)


def _ocean(bass, mid, treble):
    r = bass * 0.1 + treble * 0.2
    g = mid * 0.6 + treble * 0.5
    b = bass * 0.7 + mid * 0.7 + treble * 0.9
    return _clamp(r), _clamp(g), _clamp(b)


def _neon(bass, mid, treble):
    r = bass * 0.9
    g = treble * 0.9
    b = bass * 0.3 + mid * 0.9
    return _clamp(r), _clamp(g), _clamp(b)


def _pastel(bass, mid, treble):
    r = bass * 0.6 + mid * 0.2 + treble * 0.1
    g = mid * 0.2 + treble * 0.5
    b = bass * 0.3 + mid * 0.5 + treble * 0.4
    return _clamp(r), _clamp(g), _clamp(b)


def _mono(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    v = _clamp(brightness)
    return v, v, v


THEMES: dict[str, Theme] = {
    "arco-iris": Theme("Arco-íris", _rainbow),
    "fogo": Theme("Fogo", _fire),
    "oceano": Theme("Oceano", _ocean),
    "neon": Theme("Neon", _neon),
    "pastel": Theme("Pastel", _pastel),
    "mono": Theme("Monocromático", _mono),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["arco-iris"])
