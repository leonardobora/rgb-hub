"""CLI da central de automacao das luzes RGB (Tuya, controle local).

Uso:
    python cli.py list
    python cli.py on <nome>
    python cli.py off <nome>
    python cli.py color <nome> <hex>          # ex: FF00FF
    python cli.py brightness <nome> <pct>     # 0-100
    python cli.py scene <nome_da_cena>
    python cli.py sync screen [--lights fita quarto] [--monitor 1]
    python cli.py sync audio [--lights fita quarto] [--gain 8.0] [--no-beat] [--beat-sensitivity 1.6]
"""
import argparse
import sys

from lights import LightHub, LightNotFound
from scenes import SCENES, apply_scene


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="lista as luzes descobertas")

    p_on = sub.add_parser("on", help="liga uma luz")
    p_on.add_argument("name")

    p_off = sub.add_parser("off", help="desliga uma luz")
    p_off.add_argument("name")

    p_color = sub.add_parser("color", help="define a cor de uma luz")
    p_color.add_argument("name")
    p_color.add_argument("hex_color", help="cor em hex, ex: FF00FF")

    p_bright = sub.add_parser("brightness", help="define o brilho de uma luz")
    p_bright.add_argument("name")
    p_bright.add_argument("percent", type=int)

    p_scene = sub.add_parser("scene", help=f"aplica uma cena pronta ({', '.join(SCENES)})")
    p_scene.add_argument("name", choices=list(SCENES.keys()))

    p_sync = sub.add_parser("sync", help="sincroniza cor das luzes com tela ou audio, em loop")
    sync_sub = p_sync.add_subparsers(dest="sync_source", required=True)

    p_sync_screen = sync_sub.add_parser("screen", help="usa a cor media da tela")
    p_sync_screen.add_argument("--lights", nargs="+", default=None, help="default: todas as luzes")
    p_sync_screen.add_argument("--monitor", type=int, default=1, help="indice do monitor (mss), default: 1")

    p_sync_audio = sync_sub.add_parser("audio", help="usa o audio que esta tocando (loopback do alto-falante)")
    p_sync_audio.add_argument("--lights", nargs="+", default=None, help="default: todas as luzes")
    p_sync_audio.add_argument("--gain", type=float, default=8.0, help="sensibilidade, ajuste se ficar fraco/estourado")
    p_sync_audio.add_argument("--no-beat", action="store_true", help="desliga o flash de batida, so cor continua")
    p_sync_audio.add_argument("--beat-sensitivity", type=float, default=1.6, help="quao acima da media o grave precisa estourar pra contar como batida")

    args = parser.parse_args()

    try:
        hub = LightHub()
    except FileNotFoundError as exc:
        print(f"Erro: {exc}")
        sys.exit(1)

    try:
        if args.command == "list":
            for d in hub.list():
                print(f"{d['name']:20s} id={d['id']}  ip={d['ip']}")
        elif args.command == "on":
            hub.turn_on(args.name)
        elif args.command == "off":
            hub.turn_off(args.name)
        elif args.command == "color":
            hub.set_color(args.name, args.hex_color)
        elif args.command == "brightness":
            hub.set_brightness(args.name, args.percent)
        elif args.command == "scene":
            apply_scene(hub, args.name)
        elif args.command == "sync":
            from reactive import run

            light_names = args.lights or [d["name"] for d in hub.list()]
            if args.sync_source == "screen":
                from screen_source import screen_colors

                run(hub, light_names, screen_colors(monitor_index=args.monitor))
            elif args.sync_source == "audio":
                from audio_source import audio_colors

                source = audio_colors(
                    gain=args.gain,
                    beat_detect=not args.no_beat,
                    beat_sensitivity=args.beat_sensitivity,
                )
                run(hub, light_names, source)
    except (LightNotFound, ValueError, KeyError) as exc:
        print(f"Erro: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nEncerrando.")


if __name__ == "__main__":
    main()
