"""Icone na bandeja do Windows (system tray) pra ligar/desligar a
sincronizacao das luzes com tela ou audio, sem terminal aberto.

Uso:
    python tray.py

Clique com botao direito no icone (perto do relogio) pra abrir o menu.
O icone e um circulo dividido em 3 (vermelho/verde/azul) pra ser facil
de achar entre os outros -- nao e so uma bolinha cinza generica. O
ponto no centro mostra o estado: cinza = parado, branco = sincronizando.
"""
import threading

import pystray
from PIL import Image, ImageDraw

from lights import LightHub
from reactive import run as reactive_run
from scenes import SCENES, apply_scene

_hub = None
_thread = None
_stop_event = threading.Event()
_current_mode = None  # None | "screen" | "audio"


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

        source = audio_colors()

    _thread = threading.Thread(
        target=reactive_run,
        args=(_hub, _light_names(), source),
        kwargs={"stop_event": _stop_event},
        daemon=True,
    )
    _current_mode = mode
    _thread.start()
    icon.icon = _icon_image(True)
    icon.title = f"rgb-hub: sync {mode}"


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


def _scene_handler(name):
    def handler(icon, item):
        _stop_sync(icon)
        apply_scene(_hub, name)

    return handler


def _quit(icon, item):
    _stop_sync()
    icon.stop()


def main():
    global _hub
    _hub = LightHub()

    scene_items = [pystray.MenuItem(f"Cena: {name}", _scene_handler(name)) for name in SCENES]

    menu = pystray.Menu(
        pystray.MenuItem("Sync Tela", _toggle_screen, checked=lambda i: _current_mode == "screen"),
        pystray.MenuItem("Sync Áudio", _toggle_audio, checked=lambda i: _current_mode == "audio"),
        pystray.Menu.SEPARATOR,
        *scene_items,
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair", _quit),
    )

    icon = pystray.Icon("rgb-hub", _icon_image(False), "rgb-hub: parado", menu)
    icon.run()


if __name__ == "__main__":
    main()
