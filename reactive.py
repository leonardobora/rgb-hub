"""Loop generico: pega cores de uma fonte (tela ou audio) e aplica nas
luzes, com limite de taxa e suavizacao de cores -- senao a gente afoga
o protocolo local da Tuya de comandos e as luzes comecam a
atrasar/travar, ou as cores mudam de forma abrupta demais.
"""
import time


def _lerp(a, b, t):
    """Interpolacao linear entre dois valores."""
    return a + (b - a) * t


def _smooth_color(prev, new, factor):
    """Suaviza a transicao entre duas cores usando EMA.
    factor=0.0 = instantaneo (sem suavizacao)
    factor=0.8 = muito suave (leva ~5 frames pra chegar no alvo)
    """
    if prev is None:
        return new
    r = int(_lerp(prev[0], new[0], 1.0 - factor))
    g = int(_lerp(prev[1], new[1], 1.0 - factor))
    b = int(_lerp(prev[2], new[2], 1.0 - factor))
    return (r, g, b)


def run(hub, light_names, color_source, min_interval=0.15, min_delta=5,
        stop_event=None, smooth=0.7):
    """color_source: generator que produz (r, g, b) continuamente.

    smooth: fator de suavizacao (0.0-0.95). Quanto maior, mais lenta
    a transicao de cor. 0.7 = ~3-4 frames pra chegar no alvo.
    min_delta: delta minimo pra enviar nova cor (mais baixo = mais responsivo).

    stop_event: threading.Event opcional -- se marcado, encerra o loop
    no proximo item gerado (usado pelo tray.py pra dar toggle sem matar
    o processo inteiro).
    """
    last_sent = {name: None for name in light_names}
    last_color = None  # cor suavizada atual
    last_send_time = 0.0

    print(f"Sincronizando {', '.join(light_names)} (Ctrl+C pra parar)...")
    for r, g, b in color_source:
        if stop_event is not None and stop_event.is_set():
            break

        now = time.time()
        if now - last_send_time < min_interval:
            continue

        # suaviza a cor
        raw = (r, g, b)
        smoothed = _smooth_color(last_color, raw, smooth)
        last_color = smoothed

        r_s, g_s, b_s = smoothed
        hex_color = f"{r_s:02X}{g_s:02X}{b_s:02X}"
        for name in light_names:
            prev = last_sent[name]
            if prev is None or _delta(prev, smoothed) >= min_delta:
                try:
                    hub.set_color(name, hex_color)
                except Exception as exc:
                    print(f"  aviso: falha ao enviar cor pra '{name}': {exc}")
                last_sent[name] = smoothed
        last_send_time = now


def _delta(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))
