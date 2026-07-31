"""Loop generico: pega cores de uma fonte (tela ou audio) e aplica nas
luzes, com limite de taxa -- senao a gente afoga o protocolo local da
Tuya de comandos e as luzes comecam a atrasar/travar.
"""
import time


def run(hub, light_names, color_source, min_interval=0.15, min_delta=10, stop_event=None):
    """color_source: generator que produz (r, g, b) continuamente.

    stop_event: threading.Event opcional -- se marcado, encerra o loop
    no proximo item gerado (usado pelo tray.py pra dar toggle sem matar
    o processo inteiro).
    """
    last_sent = {name: None for name in light_names}
    last_send_time = 0.0

    print(f"Sincronizando {', '.join(light_names)} (Ctrl+C pra parar)...")
    for r, g, b in color_source:
        if stop_event is not None and stop_event.is_set():
            break

        now = time.time()
        if now - last_send_time < min_interval:
            continue

        hex_color = f"{r:02X}{g:02X}{b:02X}"
        for name in light_names:
            prev = last_sent[name]
            if prev is None or _delta(prev, (r, g, b)) >= min_delta:
                try:
                    hub.set_color(name, hex_color)
                except Exception as exc:
                    print(f"  aviso: falha ao enviar cor pra '{name}': {exc}")
                last_sent[name] = (r, g, b)
        last_send_time = now


def _delta(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))
