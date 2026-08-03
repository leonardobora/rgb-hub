"""Teste visual: toca uma musica e mostra no terminal como as cores
variam em tempo real. Roda com:

    python test_color_sync.py

Seleciona a cor que quiser testar (vermelho, azul, etc).
Pressione Ctrl+C pra parar.
"""
import sys
import numpy as np
import soundcard as sc
from color_themes import THEMES, get_theme


def test_theme(theme_name, duration_sec=10):
    theme = get_theme(theme_name)
    speaker = sc.default_speaker()
    mic = sc.get_microphone(speaker.name, include_loopback=True)

    bass_peak = 1.0
    mid_peak = 1.0
    treble_peak = 1.0

    print(f"\n=== Teste: {theme.name} ===")
    print(f" khỏa {duration_sec} segundos de audio...")
    print("Barra de intensidade:\n")

    import time
    start = time.time()

    with mic.recorder(samplerate=44100) as rec:
        while time.time() - start < duration_sec:
            data = rec.record(numframes=1024)
            mono = data.mean(axis=1) if data.ndim > 1 else data
            spectrum = np.abs(np.fft.rfft(mono))
            freqs = np.fft.rfftfreq(len(mono), d=1 / 44100)

            bass = spectrum[(freqs >= 20) & (freqs < 250)].mean()
            mid = spectrum[(freqs >= 250) & (freqs < 2000)].mean()
            treble = spectrum[(freqs >= 2000) & (freqs < 8000)].mean()

            bass_peak = max(bass, bass_peak * 0.995)
            mid_peak = max(mid, mid_peak * 0.995)
            treble_peak = max(treble, treble_peak * 0.995)

            bn = bass / bass_peak if bass_peak > 0 else 0
            mn = mid / mid_peak if mid_peak > 0 else 0
            tn = treble / treble_peak if treble_peak > 0 else 0

            r_out, g_out, b_out = theme.apply(bn, mn, tn)
            brightness = (r_out + g_out + b_out) / (3 * 255)

            bar_len = int(brightness * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)

            sys.stdout.write(
                f"\r  RGB({r_out:3d},{g_out:3d},{b_out:3d}) |{bar}| {brightness:.0%}  "
            )
            sys.stdout.flush()

    print("\n\nFim do teste!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        print("Cenas de cores disponíveis:")
        for key in ["vermelho", "azul", "verde", "branco", "roxo", "rosa", "amarelo", "ciano", "laranja"]:
            print(f"  - {key}")
        print("\nEspectro:")
        for key in ["arco-iris", "fogo", "oceano", "neon", "pastel", "mono"]:
            print(f"  - {key}")
        name = input("\nQual cena testar? ").strip() or "vermelho"

    test_theme(name)
