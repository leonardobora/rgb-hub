from unittest.mock import MagicMock, patch

from audio_sessions import AudioSession, get_session_by_name, list_active_sessions


def test_list_active_sessions_returns_list():
    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = []
        result = list_active_sessions()
        assert isinstance(result, list)


def test_list_active_sessions_filters_inactive():
    active = MagicMock()
    active.State = 1  # AudioSessionState.Active
    active.Process.name.return_value = "chrome.exe"
    active.Process.pid = 1234
    active.SimpleAudioVolume.GetMasterVolume.return_value = 0.8

    inactive = MagicMock()
    inactive.State = 0  # AudioSessionState.Inactive
    inactive.Process.name.return_value = "discord.exe"
    inactive.Process.pid = 5678
    inactive.SimpleAudioVolume.GetMasterVolume.return_value = 0.5

    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = [active, inactive]
        result = list_active_sessions()

    assert len(result) == 1
    assert result[0].name == "chrome.exe"
    assert result[0].is_active is True


def test_list_active_sessions_filters_zero_volume():
    session = MagicMock()
    session.State = 1
    session.Process.name.return_value = "spotify.exe"
    session.Process.pid = 9999
    session.SimpleAudioVolume.GetMasterVolume.return_value = 0.0

    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = [session]
        result = list_active_sessions()

    assert len(result) == 0


def test_get_session_by_name_finds_match():
    session = MagicMock()
    session.State = 1
    session.Process.name.return_value = "chrome.exe"
    session.Process.pid = 1234
    session.SimpleAudioVolume.GetMasterVolume.return_value = 0.5

    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = [session]
        result = get_session_by_name("chrome")

    assert result is not None
    assert result.name == "chrome.exe"


def test_get_session_by_name_returns_none_when_not_found():
    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = []
        result = get_session_by_name("nao-existe")

    assert result is None


def test_get_session_by_name_is_case_insensitive():
    session = MagicMock()
    session.State = 1
    session.Process.name.return_value = "Spotify.exe"
    session.Process.pid = 1111
    session.SimpleAudioVolume.GetMasterVolume.return_value = 0.5

    with patch("audio_sessions._get_all_sessions") as mock:
        mock.return_value = [session]
        result = get_session_by_name("spotify")

    assert result is not None
