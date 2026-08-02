"""Gera cores a partir do audio que esta tocando no PC (loopback do
alto-falante padrao, nao o microfone), via FFT simples em 3 bandas
(grave/medio/agudo) mapeadas pra cor via tema selecionado.

Normaliza cada banda contra seu proprio pico historico, assim grave,
medio e agudo tem escalas independentes e as cores refletem a
distribuicao real do audio (nao so a dominancia do grave).

Suporta filtragem por aplicativo de audio (via Windows Core Audio API),
temas de cor pre-definidos, e limiar de sensibilidade pra ignorar ruido.
"""
import numpy as np
import soundcard as sc

from audio_sessions import get_session_by_name
from color_themes import get_theme

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
_APP_CHECK_INTERVAL = 10


def audio_colors(gain=1.0, beat_detect=True, beat_sensitivity=1.6,
                 beat_boost=1.3, beat_min_energy=0.02,
                 theme="arco-iris", threshold=0.02, target_app=None):
    speaker = sc.default_speaker()
    loopback_mic = sc.get_microphone(speaker.name, include_loopback=True)

    bass_ema = None
    block_count = 0
    app_is_active = True
    color_func = get_theme(theme).apply

    # picos historicos por banda (pra normalizar relativo ao proprio pico)
    bass_peak = 1.0
    mid_peak = 1.0
    treble_peak = 1.0

    # medias moveis das bandas normalizadas
    bass_smooth = 0.0
    mid_smooth = 0.0
    treble_smooth = 0.0
    first_block = True

    with loopback_mic.recorder(samplerate=SAMPLE_RATE) as rec:
        while True:
            data = rec.record(numframes=BLOCK_SIZE)
            mono = data.mean(axis=1) if data.ndim > 1 else data

            spectrum = np.abs(np.fft.rfft(mono))
            freqs = np.fft.rfftfreq(len(mono), d=1 / SAMPLE_RATE)

            bass_raw = spectrum[(freqs >= 20) & (freqs < 250)].mean()
            mid_raw = spectrum[(freqs >= 250) & (freqs < 2000)].mean()
            treble_raw = spectrum[(freqs >= 2000) & (freqs < 8000)].mean()

            # atualiza picos com decay lento (pico cai 5% por frame)
            bass_peak = max(bass_raw, bass_peak * 0.995)
            mid_peak = max(mid_raw, mid_peak * 0.995)
            treble_peak = max(treble_raw, treble_peak * 0.995)

            # normaliza cada banda contra seu proprio pico (0..1)
            bass_norm = bass_raw / bass_peak if bass_peak > 0 else 0
            mid_norm = mid_raw / mid_peak if mid_peak > 0 else 0
            treble_norm = treble_raw / treble_peak if treble_peak > 0 else 0

            # suavizacao EMA
            s = 0.6
            if first_block:
                bass_smooth = bass_norm
                mid_smooth = mid_norm
                treble_smooth = treble_norm
                first_block = False
            else:
                bass_smooth = bass_smooth * s + bass_norm * (1.0 - s)
                mid_smooth = mid_smooth * s + mid_norm * (1.0 - s)
                treble_smooth = treble_smooth * s + treble_norm * (1.0 - s)

            # escala 0..1 -> 0..255
            r = int(max(0, min(255, bass_smooth * gain * 255)))
            g = int(max(0, min(255, mid_smooth * gain * 255)))
            b = int(max(0, min(255, treble_smooth * gain * 255)))

            # checa app de audio periodicamente
            block_count += 1
            if target_app and (block_count == 1 or block_count % _APP_CHECK_INTERVAL == 0):
                session = get_session_by_name(target_app)
                app_is_active = session is not None

            # limiar de sensibilidade
            energy = (bass_raw + mid_raw + treble_raw) / 3.0
            if energy < threshold or (target_app and not app_is_active):
                yield (0, 0, 0)
                continue

            # aplica tema de cor
            r, g, b = color_func(r, g, b)

            # deteccao de batida
            if beat_detect:
                if bass_ema is None:
                    bass_ema = bass_raw
                is_beat = bass_raw > beat_min_energy and bass_raw > bass_ema * beat_sensitivity
                bass_ema = bass_ema * 0.9 + bass_raw * 0.1
                if is_beat:
                    r, g, b = _flash(r, g, b, beat_boost)

            yield (r, g, b)


def _flash(r, g, b, boost):
    return tuple(_to_255(c * boost + 15) for c in (r, g, b))


def _to_255(value):
    return int(max(0, min(255, value)))
