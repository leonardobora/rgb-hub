from unittest.mock import MagicMock, patch

import numpy as np

from audio_source import audio_colors


def _make_silence_block():
    return np.zeros(1024)


def _make_loud_bass_block():
    t = np.linspace(0, 1, 1024, endpoint=False)
    return np.sin(2 * np.pi * 60 * t) * 0.8


def _fake_recorder(blocks):
    recorder = MagicMock()
    recorder.record = MagicMock(side_effect=blocks)
    return recorder


def test_default_theme_is_rainbow():
    block = _make_loud_bass_block()
    recorder = _fake_recorder([block, block])

    with patch("audio_source.sc") as mock_sc:
        speaker = MagicMock()
        mock_sc.default_speaker.return_value = speaker
        mock_sc.get_microphone.return_value.recorder.return_value.__enter__ = lambda s: recorder
        mock_sc.get_microphone.return_value.recorder.return_value.__exit__ = MagicMock(return_value=False)

        gen = audio_colors()
        r, g, b = next(gen)

    assert isinstance(r, int)
    assert isinstance(g, int)
    assert isinstance(b, int)


def test_threshold_produces_black_when_quiet():
    block = _make_silence_block()
    recorder = _fake_recorder([block, block])

    with patch("audio_source.sc") as mock_sc:
        speaker = MagicMock()
        mock_sc.default_speaker.return_value = speaker
        mock_sc.get_microphone.return_value.recorder.return_value.__enter__ = lambda s: recorder
        mock_sc.get_microphone.return_value.recorder.return_value.__exit__ = MagicMock(return_value=False)

        gen = audio_colors(threshold=0.1)
        r, g, b = next(gen)

    assert r == 0
    assert g == 0
    assert b == 0


def test_theme_fire_passes_values():
    block = _make_loud_bass_block()
    recorder = _fake_recorder([block, block])

    with patch("audio_source.sc") as mock_sc:
        speaker = MagicMock()
        mock_sc.default_speaker.return_value = speaker
        mock_sc.get_microphone.return_value.recorder.return_value.__enter__ = lambda s: recorder
        mock_sc.get_microphone.return_value.recorder.return_value.__exit__ = MagicMock(return_value=False)

        gen = audio_colors(theme="fogo", threshold=0.0)
        r, g, b = next(gen)

    assert isinstance(r, int) and 0 <= r <= 255
    assert isinstance(g, int) and 0 <= g <= 255
    assert isinstance(b, int) and 0 <= b <= 255
    assert r + g + b > 0


def test_target_app_inactive_produces_black():
    block = _make_loud_bass_block()
    recorder = _fake_recorder([block, block])

    with patch("audio_source.sc") as mock_sc, \
         patch("audio_source.get_session_by_name") as mock_session:
        speaker = MagicMock()
        mock_sc.default_speaker.return_value = speaker
        mock_sc.get_microphone.return_value.recorder.return_value.__enter__ = lambda s: recorder
        mock_sc.get_microphone.return_value.recorder.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.return_value = None

        gen = audio_colors(target_app="chrome")
        r, g, b = next(gen)

    assert r == 0
    assert g == 0
    assert b == 0


def test_target_app_active_passes_through():
    block = _make_loud_bass_block()
    recorder = _fake_recorder([block, block])

    with patch("audio_source.sc") as mock_sc, \
         patch("audio_source.get_session_by_name") as mock_session:
        speaker = MagicMock()
        mock_sc.default_speaker.return_value = speaker
        mock_sc.get_microphone.return_value.recorder.return_value.__enter__ = lambda s: recorder
        mock_sc.get_microphone.return_value.recorder.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.return_value = MagicMock(is_active=True)

        gen = audio_colors(target_app="chrome", threshold=0.0)
        r, g, b = next(gen)

    assert isinstance(r, int)
