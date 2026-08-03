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


def _solid(r_base, g_base, b_base):
    """Cria tema de cor solida: volume do audio controla brilho
    de uma cor fixa. Todos os canais mudam juntos."""
    def _apply(bass, mid, treble):
        brightness = (bass + mid + treble) / 3.0
        return _clamp(r_base * brightness), _clamp(g_base * brightness), _clamp(b_base * brightness)
    return _apply


def _color_sync(r_base, g_base, b_base):
    """Cena de cor: volume controla brilho, mas com resposta mais
    suave pra ficar mais atmosferico (usado nas cenas estaticas)."""
    def _apply(bass, mid, treble):
        brightness = (bass + mid + treble) / 3.0
        return _clamp(r_base * brightness), _clamp(g_base * brightness), _clamp(b_base * brightness)
    return _apply


# --- Cenas de cor (audio reativo com cor solida) ---

def _vermelho(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(255 * brightness), 0, 0


def _azul(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, 0, _clamp(255 * brightness)


def _verde(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, _clamp(255 * brightness), 0


def _branco(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    v = _clamp(255 * brightness)
    return v, v, v


def _roxo(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(180 * brightness), 0, _clamp(255 * brightness)


def _rosa(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(255 * brightness), 0, _clamp(128 * brightness)


def _amarelo(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(255 * brightness), _clamp(200 * brightness), 0


def _ciano(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return 0, _clamp(255 * brightness), _clamp(255 * brightness)


def _laranja(bass, mid, treble):
    brightness = (bass + mid + treble) / 3.0
    return _clamp(255 * brightness), _clamp(100 * brightness), 0


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
