"""Sobe server API (porta 8000) + dashboard (porta 8001) juntos
pra gravacao. Um unico comando pra tudo funcionar.

Uso:
    python start_all.py              # sobe os dois
    python start_all.py --demo       # sobe + roda demo automatica
    python start_all.py --port 8000  # porta do server
"""
import argparse
import os
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Sobe server + dashboard do rgb-hub")
    parser.add_argument("--port", type=int, default=8000, help="Porta do server API")
    parser.add_argument("--dashboard-port", type=int, default=8001, help="Porta do dashboard")
    parser.add_argument("--demo", action="store_true", help="Roda demo automatica apos iniciar")
    parser.add_argument("--demo-duration", type=float, default=60, help="Duracao da demo em segundos")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    print("  rgb-hub - server + dashboard")
    print("=" * 50)
    print()
    print(f"  Server API:    http://127.0.0.1:{args.port}")
    print(f"  Dashboard:     http://127.0.0.1:{args.dashboard_port}")
    print()

    env = os.environ.copy()
    env["HUB_PORT"] = str(args.port)
    env["DASHBOARD_PORT"] = str(args.dashboard_port)

    procs = []

    # server API
    print(f"  Iniciando server API na porta {args.port}...")
    server_proc = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=base_dir, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    procs.append(("server", server_proc))

    # dashboard
    print(f"  Iniciando dashboard na porta {args.dashboard_port}...")
    dash_proc = subprocess.Popen(
        [sys.executable, "dashboard.py"],
        cwd=base_dir, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    procs.append(("dashboard", dash_proc))

    time.sleep(2)

    # verifica se subiram
    for name, proc in procs:
        if proc.poll() is not None:
            print(f"  [!] {name} falhou (exit code {proc.returncode})")
            return 1

    print()
    print("  Pronto! Abra no navegador:")
    print(f"    Dashboard: http://127.0.0.1:{args.dashboard_port}")
    print()
    print("  Pra gravar:")
    print("    1. Abra o dashboard no navegador")
    print("    2. Abra o terminal ao lado")
    print("    3. Inicie a gravacao com OBS/ShareX")
    print()

    if args.demo:
        print("  Rodando demo automatica...")
        time.sleep(1)
        demo_proc = subprocess.Popen(
            [sys.executable, "demo.py", "--duration", str(args.demo_duration)],
            cwd=base_dir, env=env,
        )
        procs.append(("demo", demo_proc))

    try:
        print("  Ctrl+C pra parar tudo\n")
        while True:
            for name, proc in procs:
                if proc.poll() is not None:
                    print(f"  [!] {name} parou inesperadamente")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Parando...")
        for name, proc in procs:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        print("  Pronto!")


if __name__ == "__main__":
    sys.exit(main() or 0)
