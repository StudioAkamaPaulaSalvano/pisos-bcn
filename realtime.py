#!/usr/bin/env python3
"""
MODO TIEMPO REAL — para una máquina encendida siempre (PC de la oficina).

Revisa cada ~60s, regenera la página, y la SIRVE en http://localhost:8000
(desde el móvil en la misma wifi: http://IP-DE-ESTA-COMPU:8000).
Mucho más rápido y fiable que la nube.

Uso:
    python realtime.py            # cada 60s, sirve en puerto 8000
    python realtime.py 30         # cada 30s
    python realtime.py 60 8080    # cada 60s, puerto 8080

Requisitos (una sola vez):
    pip install requests beautifulsoup4 lxml playwright
    python -m playwright install chromium
"""
import sys, time, subprocess, os, threading, http.server, socketserver

HERE = os.path.dirname(os.path.abspath(__file__))
WEBDIR = os.path.join(HERE, "app", "web")
PY = sys.executable
INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000


def serve():
    os.makedirs(WEBDIR, exist_ok=True)
    Handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=WEBDIR, **k)
    socketserver.TCPServer.allow_reuse_address = True
    # SOLO localhost: solo esta computadora puede abrirlo. Nadie de la red/oficina
    # lo ve, no se expone ninguna IP ni nada a internet.
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"🌐 Página (privada, solo en esta compu): http://localhost:{PORT}")


def run(mod):
    args = [PY, os.path.join(HERE, "app", mod)] + (["--fast"] if mod == "scrape.py" else [])
    subprocess.run(args, cwd=HERE, check=False)


def main():
    serve()
    print(f"⏱️  Modo tiempo real: reviso cada {INTERVAL}s. (Ctrl+C para parar)")
    n = 0
    while True:
        n += 1
        t0 = time.time()
        print(f"\n— ciclo {n} —", flush=True)
        try:
            run("scrape.py"); run("build_page.py"); run("notify.py")
        except Exception as e:
            print("error en ciclo:", e)
        dt = int(time.time() - t0)
        wait = max(5, INTERVAL - dt)
        print(f"ciclo en {dt}s · próximo en {wait}s", flush=True)
        time.sleep(wait)


if __name__ == "__main__":
    main()
