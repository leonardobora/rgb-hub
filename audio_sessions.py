"""Detecta sessoes de audio ativas no Windows via Core Audio API (pycaw).

Permite identificar quais aplicativos estao produzindo som no momento,
pra filtrar a captura de loopback e reagir só ao audio de um app
especifico.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from pycaw.pycaw import AudioUtilities
    import comtypes
    _HAS_PYCAW = True
except ImportError:
    _HAS_PYCAW = False


@dataclass
class AudioSession:
    name: str
    display_name: str
    pid: int
    volume: float
    is_active: bool


def _get_all_sessions():
    if not _HAS_PYCAW:
        return []
    return AudioUtilities.GetAllSessions()


def list_active_sessions() -> list[AudioSession]:
    sessions = []
    for s in _get_all_sessions():
        try:
            proc = s.Process
            if proc is None:
                continue
            state = s.State
            volume = s.SimpleAudioVolume.GetMasterVolume()
            if state != 1 or volume <= 0:
                continue
            sessions.append(AudioSession(
                name=proc.name(),
                display_name=proc.name().replace(".exe", ""),
                pid=proc.pid,
                volume=volume,
                is_active=True,
            ))
        except Exception:
            continue
    return sessions


def get_session_by_name(name: str) -> AudioSession | None:
    name_lower = name.lower()
    for session in list_active_sessions():
        if name_lower in session.name.lower():
            return session
    return None
