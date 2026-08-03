from color_themes import THEMES, Theme, get_theme


def test_all_themes_exist():
    expected = {
        "arco-iris", "fogo", "oceano", "neon", "pastel", "mono",
        "vermelho", "azul", "verde", "branco", "roxo", "rosa",
        "amarelo", "ciano", "laranja",
    }
    assert set(THEMES.keys()) == expected


def test_all_themes_return_rgb_tuple():
    for name, theme in THEMES.items():
        r, g, b = theme.apply(0.0, 0.0, 0.0)
        assert isinstance(r, int)
        assert isinstance(g, int)
        assert isinstance(b, int)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


def test_all_themes_handle_max_input():
    for name, theme in THEMES.items():
        r, g, b = theme.apply(1.0, 1.0, 1.0)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255


def test_rainbow_theme_maps_01_to_255():
    theme = get_theme("arco-iris")
    r, g, b = theme.apply(0.4, 0.6, 0.8)
    assert r == 102  # 0.4 * 255
    assert g == 153  # 0.6 * 255
    assert b == 204  # 0.8 * 255


def test_fire_theme_is_warm():
    theme = get_theme("fogo")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r > b


def test_ocean_theme_is_cool():
    theme = get_theme("oceano")
    r, g, b = theme.apply(0.2, 0.4, 0.8)
    assert b > r


def test_mono_theme_produces_grayscale():
    theme = get_theme("mono")
    r, g, b = theme.apply(0.4, 0.6, 0.8)
    assert r == g == b


def test_mono_theme_brightness_scales():
    theme = get_theme("mono")
    r1, _, _ = theme.apply(0.2, 0.2, 0.2)
    r2, _, _ = theme.apply(0.8, 0.8, 0.8)
    assert r2 > r1


def test_get_theme_returns_default_for_unknown():
    theme = get_theme("nao-existe")
    assert theme.name == "Arco-íris"


def test_get_theme_returns_correct_theme():
    theme = get_theme("fogo")
    assert theme.name == "Fogo"


def test_red_theme_is_only_red():
    theme = get_theme("vermelho")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r > 0
    assert g == 0
    assert b == 0


def test_red_theme_scales_with_volume():
    theme = get_theme("vermelho")
    r1, _, _ = theme.apply(0.2, 0.1, 0.05)
    r2, _, _ = theme.apply(0.9, 0.5, 0.3)
    assert r2 > r1


def test_blue_theme_is_only_blue():
    theme = get_theme("azul")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r == 0
    assert g == 0
    assert b > 0


def test_green_theme_is_only_green():
    theme = get_theme("verde")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r == 0
    assert g > 0
    assert b == 0


def test_white_theme_is_grayscale():
    theme = get_theme("branco")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r == g == b


def test_purple_theme_has_red_and_blue():
    theme = get_theme("roxo")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r > 0
    assert g == 0
    assert b > 0


def test_cyan_theme_has_green_and_blue():
    theme = get_theme("ciano")
    r, g, b = theme.apply(0.8, 0.4, 0.2)
    assert r == 0
    assert g > 0
    assert b > 0


def test_color_themes_silence_is_black():
    for name in ["vermelho", "azul", "verde", "branco", "roxo", "rosa", "amarelo", "ciano", "laranja"]:
        theme = get_theme(name)
        r, g, b = theme.apply(0.0, 0.0, 0.0)
        assert r == 0 and g == 0 and b == 0, f"{name} should be black at silence"
