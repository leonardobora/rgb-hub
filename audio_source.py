"""Gera cores a partir do audio que esta tocando no PC (loopback do
alto-falante padrao, nao o microfone), via FFT simples em 3 bandas
(grave/medio/agudo) mapeadas pra R/G/B.

Deteccao de batida: reaproveita o mesmo FFT que ja calculamos pra cor
(nao roda nenhum processamento extra pesado) -- so mantem uma media
movel exponencial da energia do grave e compara o bloco atual contra
ela. Quando o grave atual estoura acima da media por um fator, conta
como batida e da um flash de brilho naquele frame. Custo extra por
bloco: ~3 operacoes escalares, irrelevante em CPU.
"""
import numpy as np
import soundcard as sc

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024


def audio_colors(gain=8.0, beat_detect=True, beat_sensitivity=1.6, beat_boost=1.8, beat_min_energy=0.02):
    speaker = sc.default_speaker()
    loopback_mic = sc.get_microphone(speaker.name, include_loopback=True)

    bass_ema = None  # media movel da energia do grave, pra comparar contra o bloco atual

    with loopback_mic.recorder(samplerate=SAMPLE_RATE) as rec:
        while True:
            data = rec.record(numframes=BLOCK_SIZE)
            mono = data.mean(axis=1) if data.ndim > 1 else data

            spectrum = np.abs(np.fft.rfft(mono))
            freqs = np.fft.rfftfreq(len(mono), d=1 / SAMPLE_RATE)

            bass = spectrum[(freqs >= 20) & (freqs < 250)].mean()
            mid = spectrum[(freqs >= 250) & (freqs < 2000)].mean()
            treble = spectrum[(freqs >= 2000) & (freqs < 8000)].mean()

            r, g, b = _to_255(bass * gain), _to_255(mid * gain), _to_255(treble * gain)

            if beat_detect:
                if bass_ema is None:
                    bass_ema = bass
                is_beat = bass > beat_min_energy and bass > bass_ema * beat_sensitivity
                bass_ema = bass_ema * 0.9 + bass * 0.1  # decai devagar, sobe rapido no proximo beat
                if is_beat:
                    r, g, b = _flash(r, g, b, beat_boost)

            yield (r, g, b)


def _flash(r, g, b, boost):
    return tuple(_to_255(c * boost + 30) for c in (r, g, b))


def _to_255(value):
    return int(max(0, min(255, value)))
