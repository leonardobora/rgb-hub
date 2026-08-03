"""Icone na bandeja do Windows (system tray) pra ligar/desligar a
sincronizacao das luzes com tela ou audio, sem terminal aberto.

Uso:
    python tray.py

Clique com botao direito no icone (perto do relogio) pra abrir o menu.
O icone e um circulo dividido em 3 (vermelho/verde/azul em 3 fatias) pra
ser facil de achar entre os outros. O ponto no centro mostra o estado:
cinza = parado, branco = sincronizando.

Menu de audio permite escolher:
- App de audio (filtra qual app a cena reage)
- Tema de cor (paleta de mapeamento frequencia -> cor)
- Sensibilidade (limiar minimo de energia pra reagir)
- Transicao (suavizacao das mudancas de cor)
"""
import threading
import time
import webbrowser

import pystray
from PIL import Image, ImageDraw

from color_themes import THEMES
from lights import LightHub
from reactive import run as reactive_run
from scenes import SCENES, apply_scene

_hub = None
_thread = None
_stop_event = threading.Event()
_current_mode = None  # None | "screen" | "audio"
_current_theme = "arco-iris"
_current_threshold = 0.02
_current_app = None  # None = todos os apps
_current_smooth = 0.7  # suavizacao de cor (0.0-0.95)
_icon_ref = None  # referencia pro icon pra atualizar titulo

REPO_URL = "https://github.com/leonardobora/rgb-hub"
BUYMEACOFFEE_URL = "https://buymeacoffee.com/leonardobora"

SENSITIVITY_OPTIONS = [
    ("20 (baixa)", 0.2),
    ("40", 0.4),
    ("60", 0.6),
    ("80 (alta)", 0.8),
]

SMOOTH_OPTIONS = [
    ("Sem suavização", 0.0),
    ("Sutil", 0.4),
    ("Normal", 0.7),
    ("Muito suave", 0.85),
    ("Ultra suave", 0.92),
]

# separa temas em categorias pro menu
SPECTRUM_THEMES = ["arco-iris", "fogo", "oceano", "neon", "pastel", "mono"]
COLOR_THEMES = ["vermelho", "azul", "verde", "branco", "roxo", "rosa", "amarelo", "ciano", "laranja"]


def _icon_image(active):
    """Circulo RGB (vermelho/verde/azul em 3 fatias) -- se destaca dos
    outros icones do tray, que sao quase todos azuis/monocromaticos.
    O ponto central indica se ta sincronizando (branco) ou parado (cinza).
    """
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.pieslice((4, 4, 60, 60), start=-90, end=30, fill=(230, 50, 50))
    draw.pieslice((4, 4, 60, 60), start=30, end=150, fill=(40, 200, 90))
    draw.pieslice((4, 4, 60, 60), start=150, end=270, fill=(50, 100, 230))
    draw.ellipse((4, 4, 60, 60), outline="white", width=2)
    dot_color = "white" if active else (90, 90, 90)
    draw.ellipse((24, 24, 40, 40), fill=dot_color, outline="black", width=1)
    return img


def _notify(icon, message, duration=2.0):
    """Feedback visual: atualiza titulo do tray por `duration` segundos."""
    if icon is not None:
        original_title = icon.title
        icon.title = f"rgb-hub: {message}"
        threading.Timer(duration, lambda: setattr(icon, 'title', original_title)).start()


def _light_names():
    return [d["name"] for d in _hub.list()]


def _start(mode, icon):
    global _thread, _current_mode
    _stop_sync(icon)

    _stop_event.clear()
    if mode == "screen":
        from screen_source import screen_colors

        source = screen_colors()
    else:
        from audio_source import audio_colors

        source = audio_colors(
            theme=_current_theme,
            threshold=_current_threshold,
            target_app=_current_app,
        )

    _thread = threading.Thread(
        target=reactive_run,
        args=(_hub, _light_names(), source),
        kwargs={"stop_event": _stop_event, "smooth": _current_smooth},
        daemon=True,
    )
    _current_mode = mode
    _thread.start()
    icon.icon = _icon_image(True)
    theme_name = THEMES[_current_theme].name
    icon.title = f"rgb-hub: {theme_name}"


def _stop_sync(icon=None):
    global _current_mode, _thread
    _stop_event.set()
    if _thread is not None and _thread.is_alive():
        _thread.join(timeout=2)
    _current_mode = None
    if icon is not None:
        icon.icon = _icon_image(False)
        icon.title = "rgb-hub: parado"


def _toggle_screen(icon, item):
    _start("screen", icon) if _current_mode != "screen" else _stop_sync(icon)


def _toggle_audio(icon, item):
    _start("audio", icon) if _current_mode != "audio" else _stop_sync(icon)


def _set_theme(name):
    def handler(icon, item):
        global _current_theme
        _current_theme = name
        theme_name = THEMES[name].name
        _notify(icon, f"Tema: {theme_name}")
        # se ja ta sincronizando, reinicia com o novo tema
        if _current_mode == "audio":
            _start("audio", icon)
    return handler


def _set_sensitivity(value):
    def handler(icon, item):
        global _current_threshold
        _current_threshold = value
        _notify(icon, f"Sensibilidade: {int(value * 100)}")
    return handler


def _set_smooth(value):
    def handler(icon, item):
        global _current_smooth
        _current_smooth = value
        label = next((l for l, v in SMOOTH_OPTIONS if abs(v - value) < 0.01), "?")
        _notify(icon, f"Transição: {label}")
    return handler


def _set_app(name):
    def handler(icon, item):
        global _current_app
        _current_app = name
        display = name.title() if name else "Todos"
        _notify(icon, f"App: {display}")
    return handler


def _open_url(url):
    def handler(icon, item):
        webbrowser.open(url)
    return handler


def _scene_handler(name):
    def handler(icon, item):
        _stop_sync(icon)
        apply_scene(_hub, name)
        _notify(icon, f"Cena: {name}")
    return handler


def _quit(icon, item):
    _stop_sync()
    icon.stop()


def _build_audio_app_menu():
    """Build app submenu with active audio sessions."""
    try:
        from audio_sessions import list_active_sessions
        sessions = list_active_sessions()
    except Exception:
        sessions = []

    items = [
        pystray.MenuItem(
            "Todos (sistema)",
            _set_app(None),
            checked=lambda i: _current_app is None,
        ),
    ]

    for s in sessions:
        display = s.display_name.title()
        items.append(pystray.MenuItem(
            display,
            _set_app(s.name),
            checked=lambda i, n=s.name: _current_app == n,
        ))

    if not sessions:
        items.append(pystray.MenuItem(
            "(nenhum app ativo)",
            None,
            enabled=False,
        ))

    return items


def _build_spectrum_theme_menu():
    """Build spectrum theme submenu (rainbow, fire, ocean, etc.)."""
    items = []
    for key in SPECTRUM_THEMES:
        theme = THEMES[key]
        items.append(pystray.MenuItem(
            theme.name,
            _set_theme(key),
            checked=lambda i, k=key: _current_theme == k,
        ))
    return items


def _build_color_theme_menu():
    """Build solid color theme submenu (vermelho, azul, verde, etc.)."""
    items = []
    for key in COLOR_THEMES:
        theme = THEMES[key]
        items.append(pystray.MenuItem(
            theme.name,
            _set_theme(key),
            checked=lambda i, k=key: _current_theme == k,
        ))
    return items


def _build_sensitivity_menu():
    """Build sensitivity submenu."""
    items = []
    for label, value in SENSITIVITY_OPTIONS:
        items.append(pystray.MenuItem(
            label,
            _set_sensitivity(value),
            checked=lambda i, v=value: _current_threshold == v,
        ))
    return items


def _build_smooth_menu():
    """Build smoothing submenu."""
    items = []
    for label, value in SMOOTH_OPTIONS:
        items.append(pystray.MenuItem(
            label,
            _set_smooth(value),
            checked=lambda i, v=value: abs(_current_smooth - v) < 0.01,
        ))
    return items


def main():
    global _hub, _icon_ref
    _hub = LightHub()

    scene_items = [pystray.MenuItem(f"Cena: {name}", _scene_handler(name)) for name in SCENES]

    menu = pystray.Menu(
        pystray.MenuItem("Sync Tela", _toggle_screen, checked=lambda i: _current_mode == "screen"),
        pystray.MenuItem("Sync Áudio", _toggle_audio, checked=lambda i: _current_mode == "audio"),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🎨 Espectro", pystray.Menu(*_build_spectrum_theme_menu())),
        pystray.MenuItem("🔴 Cores", pystray.Menu(*_build_color_theme_menu())),
        pystray.MenuItem("📱 App de Áudio", pystray.Menu(*_build_audio_app_menu())),
        pystray.MenuItem("🎚 Sensibilidade", pystray.Menu(*_build_sensitivity_menu())),
        pystray.MenuItem("✨ Transição", pystray.Menu(*_build_smooth_menu())),
        pystray.Menu.SEPARATOR,
        *scene_items,
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⭐ Repo no GitHub", _open_url(REPO_URL)),
        pystray.MenuItem("☕ Buy Me a Coffee", _open_url(BUYMEACOFFEE_URL)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair", _quit),
    )

    icon = pystray.Icon("rgb-hub", _icon_image(False), "rgb-hub: parado", menu)
    _icon_ref = icon
    icon.run()


if __name__ == "__main__":
    main()
