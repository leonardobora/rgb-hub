"""Demo automatica pra gravacao: roda sequencia de cenas e cores
com delays cinematicos. Mostra o dashboard atualizando em tempo real.

Uso:
    python demo.py                  # roda demo completa (~60s)
    python demo.py --duration 30    # limita a 30s
    python demo.py --no-server      # so roda as cenas, sem dashboard
"""
import argparse
import time
import sys

try:
    import requests
    BASE_URL = "http://127.0.0.1:8000"
except ImportError:
    requests = None
    BASE_URL = ""

# sequencia de demo: (acao, delay_proximo)
DEMO_SEQUENCE = [
    # intro
    ({"action": "scene", "name": "foco"}, 3.0, " Cena: Foco (branco maximo)"),

    # cores solidas com audio
    ({"action": "color", "name": "fita", "hex": "FF0000"}, 2.5, " Vermelho"),
    ({"action": "color", "name": "quarto", "hex": "FF0000"}, 0.3, ""),
    ({"action": "sync", "mode": "audio"}, 4.0, " Sync audio + vermelho"),

    ({"action": "sync", "mode": "off"}, 1.0, ""),
    ({"action": "color", "name": "fita", "hex": "0000FF"}, 0.3, ""),
    ({"action": "color", "name": "quarto", "hex": "0000FF"}, 0.3, " Azul"),
    ({"action": "sync", "mode": "audio"}, 4.0, " Sync audio + azul"),

    ({"action": "sync", "mode": "off"}, 1.0, ""),
    ({"action": "color", "name": "fita", "hex": "00FF00"}, 0.3, ""),
    ({"action": "color", "name": "quarto", "hex": "00FF00"}, 0.3, " Verde"),
    ({"action": "sync", "mode": "audio"}, 4.0, " Sync audio + verde"),

    # espectro
    ({"action": "sync", "mode": "off"}, 1.0, ""),
    ({"action": "scene", "name": "gaming"}, 3.0, " Cena: Gaming"),

    # fades rapidos
    ({"action": "color", "name": "fita", "hex": "FF00FF"}, 0.5, " Magenta"),
    ({"action": "color", "name": "fita", "hex": "00FFFF"}, 0.5, " Ciano"),
    ({"action": "color", "name": "fita", "hex": "FFFF00"}, 0.5, " Amarelo"),
    ({"action": "color", "name": "fita", "hex": "FF8800"}, 0.5, " Laranja"),
    ({"action": "color", "name": "fita", "hex": "FF0044"}, 0.5, " Rosa"),
    ({"action": "color", "name": "fita", "hex": "8800FF"}, 1.0, " Roxo"),

    # final
    ({"action": "scene", "name": "foco"}, 2.0, " Cena: Foco"),
    ({"action": "scene", "name": "gaming"}, 0, " Fim da demo"),
]


def send_command(cmd: dict) -> tuple[int, str]:
    """Envia comando pro server e retorna (status, mensagem)."""
    if not requests:
        return 0, "requests nao instalado"

    action = cmd["action"]
    url = f"{BASE_URL}/{action}"
    body = {k: v for k, v in cmd.items() if k != "action"}

    try:
        r = requests.post(url, json=body, timeout=5)
        data = r.json()
        return r.status_code, data.get("message", data.get("error", ""))
    except requests.ConnectionError:
        return 0, "server offline"
    except Exception as e:
        return 0, str(e)


def run_demo(duration: float = 60.0, with_server: bool = True):
    print("=" * 50)
    print("  rgb-hub DEMO")
    print("  Gravando tela: janela do dashboard + terminal")
    print("=" * 50)
    print()

    if with_server and not requests:
        print("[!] 'requests' nao instalado. Instale com: pip install requests")
        print("    Rodando sem servidor (apenas visual)\n")
        with_server = False

    start = time.time()

    for i, (cmd, delay, label) in enumerate(DEMO_SEQUENCE):
        if time.time() - start > duration:
            break

        if with_server:
            status, msg = send_command(cmd)
            status_str = f"[{status}]" if status else "[--]"
        else:
            status_str = "[--]"
            msg = ""

        action = cmd["action"]
        detail = f"{action}: {cmd.get('name', '')} {cmd.get('hex', '')} {cmd.get('mode', '')}".strip()
        print(f"  {status_str} {detail}{f'  {label}' if label else ''}")

        if delay > 0 and time.time() - start + delay <= duration:
            time.sleep(delay)

    elapsed = time.time() - start
    print(f"\n  Demo finalizada em {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Demo automatica do rgb-hub")
    parser.add_argument("--duration", type=float, default=60.0, help="Duracao maxima em segundos")
    parser.add_argument("--no-server", action="store_true", help="Roda sem enviar pro server")
    args = parser.parse_args()

    try:
        run_demo(duration=args.duration, with_server=not args.no_server)
    except KeyboardInterrupt:
        print("\n  Demo interrompida")


if __name__ == "__main__":
    main()
