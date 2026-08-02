from color_themes import THEMES, Theme, get_theme


def test_all_themes_exist():
    expected = {"arco-iris", "fogo", "oceano", "neon", "pastel", "mono"}
    assert set(THEMES.keys()) == expected


def test_all_themes_return_rgb_tuple():
    for name, theme in THEMES.items():
        r, g, b = theme.apply(0, 0, 0)
        assert isinstance(r, int)
        assert isinstance(g, int)
        assert isinstance(b, int)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


def test_all_themes_handle_max_input():
    for name, theme in THEMES.items():
        r, g, b = theme.apply(255, 255, 255)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


def test_rainbow_theme_passes_through():
    theme = get_theme("arco-iris")
    r, g, b = theme.apply(100, 150, 200)
    assert r == 100
    assert g == 150
    assert b == 200


def test_fire_theme_is_warm():
    theme = get_theme("fogo")
    r, g, b = theme.apply(200, 100, 50)
    assert r > b


def test_ocean_theme_is_cool():
    theme = get_theme("oceano")
    r, g, b = theme.apply(50, 100, 200)
    assert b > r


def test_mono_theme_produces_grayscale():
    theme = get_theme("mono")
    r, g, b = theme.apply(100, 150, 200)
    assert r == g == b


def test_mono_theme_brightness_scales():
    theme = get_theme("mono")
    r1, _, _ = theme.apply(50, 50, 50)
    r2, _, _ = theme.apply(200, 200, 200)
    assert r2 > r1


def test_get_theme_returns_default_for_unknown():
    theme = get_theme("nao-existe")
    assert theme.name == "Arco-íris"


def test_get_theme_returns_correct_theme():
    theme = get_theme("fogo")
    assert theme.name == "Fogo"
