"""Gerencia um loop de sync (screen/audio) em thread de fundo, com
parada via threading.Event -- o mesmo padrao do tray.py, isolado pra o
server.py poder ligar/desligar por HTTP."""
import threading

from reactive import run as reactive_run


class SyncManager:
    def __init__(self, hub):
        self._hub = hub
        self._thread = None
        self._stop = threading.Event()
        self._mode = None

    @property
    def mode(self):
        return self._mode

    def is_running(self):
        return self._mode is not None

    def start(self, mode, light_names=None):
        if mode not in ("screen", "audio"):
            raise ValueError(f"Modo invalido: '{mode}'. Use 'screen' ou 'audio'.")
        self.stop()
        self._stop.clear()
        if mode == "screen":
            from screen_source import screen_colors

            source = screen_colors()
        else:
            from audio_source import audio_colors

            source = audio_colors()
        names = light_names or [d["name"] for d in self._hub.list()]
        self._mode = mode
        self._thread = threading.Thread(
            target=reactive_run,
            args=(self._hub, names, source),
            kwargs={"stop_event": self._stop},
            daemon=True,
        )
        self._thread.start()
        return {"mode": mode, "lights": names}

    def stop(self):
        if self._thread is None:
            return {"mode": None}
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        self._mode = None
        return {"mode": None}
