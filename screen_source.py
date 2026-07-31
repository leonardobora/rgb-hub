"""Gera cores a partir da cor DOMINANTE da tela (nao a media crua).

Media simples de RGB cancela cores complementares e tende pra
cinza/branco/lilas quando a tela tem conteudo misto (fundo escuro +
texto branco + elementos coloridos). Aqui a gente converte os pixels
amostrados pra HSV, ignora os que tem pouca saturacao/brilho (fundo
preto, texto branco/cinza -- eles nao "sao" uma cor), e tira a media
circular do matiz (ponderada por saturacao*valor) dos que sobraram.
Satura um pouco mais o resultado pra compensar a perda natural da
media e a cor sair "viva" na luz, nao pastel.
"""
import colorsys
import time

import mss
import numpy as np


def screen_colors(monitor_index=1, sample_step=24, fps=8, saturation_boost=1.6):
    """Gera (r, g, b) continuamente com base na cor dominante da tela.

    fps baixo de proposito: a tela nao precisa ser lida mais rapido do
    que o `reactive.py` consegue mandar comando pras luzes (~6-7/s), e
    capturar a 30fps deixa o processo comendo um nucleo inteiro de CPU.
    """
    delay = 1.0 / fps
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        while True:
            start = time.time()
            frame = np.array(sct.grab(monitor))  # BGRA
            sample = frame[::sample_step, ::sample_step, :3][..., ::-1]  # -> RGB
            yield _dominant_color(sample, saturation_boost)

            elapsed = time.time() - start
            if elapsed < delay:
                time.sleep(delay - elapsed)


def _dominant_color(rgb_pixels_0_255, saturation_boost):
    rgb = rgb_pixels_0_255.reshape(-1, 3).astype(np.float64) / 255.0
    h, s, v = _rgb_to_hsv(rgb)

    weight = s * v  # pixels sem cor (preto/branco/cinza) contam pouco
    weight_sum = weight.sum()
    if weight_sum < 1e-6:
        gray = int(np.clip(v.mean() * 255, 0, 255))
        return (gray, gray, gray)

    angles = h * 2 * np.pi
    sin_mean = np.sum(np.sin(angles) * weight) / weight_sum
    cos_mean = np.sum(np.cos(angles) * weight) / weight_sum
    mean_hue = (np.arctan2(sin_mean, cos_mean) / (2 * np.pi)) % 1.0

    mean_value = float(np.sum(v * weight) / weight_sum)
    mean_sat = min(1.0, float(np.sum(s * weight) / weight_sum) * saturation_boost)

    r, g, b = colorsys.hsv_to_rgb(mean_hue, mean_sat, mean_value)
    return (int(r * 255), int(g * 255), int(b * 255))


def _rgb_to_hsv(rgb):
    """RGB (...,3) em 0..1 -> H,S,V vetorizado (equivalente ao colorsys, mas pra array)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = rgb.max(axis=-1)
    minc = rgb.min(axis=-1)
    v = maxc
    delta = maxc - minc

    s = np.divide(delta, maxc, out=np.zeros_like(maxc), where=maxc != 0)

    safe_delta = np.where(delta == 0, 1, delta)
    rc = (maxc - r) / safe_delta
    gc = (maxc - g) / safe_delta
    bc = (maxc - b) / safe_delta

    h = np.zeros_like(maxc)
    h = np.where(maxc == r, bc - gc, h)
    h = np.where(maxc == g, 2.0 + rc - bc, h)
    h = np.where(maxc == b, 4.0 + gc - rc, h)
    h = np.where(delta == 0, 0, h)
    h = (h / 6.0) % 1.0
    return h, s, v
