#!/usr/bin/env python3
"""
MODO TIEMPO REAL (para una máquina encendida siempre, ej. el PC de la oficina).

Revisa cada ~60 segundos y regenera la página. Mucho más rápido que la nube (5 min).
Uso:
    python realtime.py            # cada 60s
    python realtime.py 30         # cada 30s

Requisitos (una sola vez, en esa máquina):
    pip install requests beautifulsoup4 lxml playwright
    python -m playwright install chromium

La página queda en app/web/index.html (ábrela en el navegador; se refresca sola).
Si configuras las variables SMTP_* también te manda email de lo nuevo.
"""
import sys, time, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
INTERVAL = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PY = sys.executable


def run(mod):
    subprocess.run([PY, os.path.join(HERE, "app", mod)] +
                   (["--fast"] if mod == "scrape.py" else []),
                   cwd=HERE, check=False)


print(f"⏱️  Modo tiempo real: revisando cada {INTERVAL}s. Ctrl+C para parar.")
n = 0
while True:
    n += 1
    t0 = time.time()
    print(f"\n— ciclo {n} —")
    run("scrape.py")
    run("build_page.py")
    run("notify.py")
    dt = time.time() - t0
    wait = max(5, INTERVAL - int(dt))
    print(f"ciclo en {int(dt)}s · próximo en {wait}s")
    time.sleep(wait)
