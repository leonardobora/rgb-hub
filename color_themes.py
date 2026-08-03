"""Paletas de cores pre-definidas mapeando bandas de frequencia (grave/
medio/agudo) pra RGB. Cada tema recebe valores das bandas em 0..1
(escala normalizada com gain) e retorna (r, g, b) em 0..255.
"""
from dataclasses import dataclass
from typing import Callable


ThemeFunc = Callable[[float, float, float], tuple[int, int, int]]


@dataclass
class Theme:
    name: str
    apply: ThemeFunc


def _clamp(value):
    return int(max(0, min(255, value)))


# --- Espectro (cores diferentes por banda, input 0..1, output 0..255) ---

def _rainbow(bass, mid, treble):
    return _clamp(bass * 255), _clamp(mid * 255), _clamp(treble * 255)


def _fire(bass, mid, treble):
    r = bass * 0.7 + mid * 0.3
    g = mid * 0.6 + treble * 0.4
    b = treble * 0.3
    return _clamp(r * 255), _clamp(g * 255), _clamp(b * 255)


def _ocean(bass, mid, treble):
    r = bass * 0.1 + treble * 0.2
    g = mid * 0.6 + treble * 0.5
    b = bass * 0.7 + mid * 0.7 + treble * 0.9
    return _clamp(r * 255), _clamp(g * 255), _clamp(b * 255)


def _neon(bass, mid, treble):
    r = bass * 0.9
    g = treble * 0.9
    b = bass * 0.3 + mid * 0.9
    return _clamp(r * 255), _clamp(g * 255), _clamp(b * 255)


def _pastel(bass, mid, treble):
    r = bass * 0.6 + mid * 0.2 + treble * 0.1
    g = mid * 0.2 + treble * 0.5
    b = bass * 0.3 + mid * 0.5 + treble * 0.4
    return _clamp(r * 255), _clamp(g * 255), _clamp(b * 255)


def _mono(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    v = _clamp(brightness * 255)
    return v, v, v


# --- Cenas de cor (audio reativo com cor solida, input 0..1) ---

def _vermelho(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(brightness * 255), 0, 0


def _azul(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, 0, _clamp(brightness * 255)


def _verde(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, _clamp(brightness * 255), 0


def _branco(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    v = _clamp(brightness * 255)
    return v, v, v


def _roxo(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(brightness * 180), 0, _clamp(brightness * 255)


def _rosa(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(brightness * 255), 0, _clamp(brightness * 128)


def _amarelo(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(brightness * 255), _clamp(brightness * 200), 0


def _ciano(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, _clamp(brightness * 255), _clamp(brightness * 255)


def _laranja(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(brightness * 255), _clamp(brightness * 100), 0


THEMES: dict[str, Theme] = {
    # Espectro (cores diferentes por banda)
    "arco-iris": Theme("Arco-íris", _rainbow),
    "fogo": Theme("Fogo", _fire),
    "oceano": Theme("Oceano", _ocean),
    "neon": Theme("Neon", _neon),
    "pastel": Theme("Pastel", _pastel),
    "mono": Theme("Monocromático", _mono),
    # Cenas de cor (audio controla brilho de cor solida)
    "vermelho": Theme("Vermelho", _vermelho),
    "azul": Theme("Azul", _azul),
    "verde": Theme("Verde", _verde),
    "branco": Theme("Branco", _branco),
    "roxo": Theme("Roxo", _roxo),
    "rosa": Theme("Rosa", _rosa),
    "amarelo": Theme("Amarelo", _amarelo),
    "ciano": Theme("Ciano", _ciano),
    "laranja": Theme("Laranja", _laranja),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["arco-iris"])
