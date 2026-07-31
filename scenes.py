"""Cenas: mapeiam luzes (por alias) pra uma cor+brilho especifico.

Aliases reais (ver aliases.json): 'fita' = LED Strip Monster (MONITOR),
'quarto' = lampada bocal Elgin (Bedroom).
"""

SCENES = {
    "gaming": {
        "fita": {"color": "8000FF", "brightness": 80},
        "quarto": {"color": "FF0040", "brightness": 60},
    },
    "foco": {
        "fita": {"color": "FFFFFF", "brightness": 100},
        "quarto": {"color": "FFFFFF", "brightness": 100},
    },
    "alerta": {
        "fita": {"color": "FF0000", "brightness": 100},
        "quarto": {"color": "FF0000", "brightness": 100},
    },
}


def apply_scene(hub, scene_name):
    if scene_name not in SCENES:
        raise KeyError(f"Cena '{scene_name}' nao existe. Opcoes: {', '.join(SCENES)}")
    for light_name, settings in SCENES[scene_name].items():
        hub.turn_on(light_name)
        hub.set_color(light_name, settings["color"])
        hub.set_brightness(light_name, settings["brightness"])
