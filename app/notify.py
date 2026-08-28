#!/usr/bin/env python3
"""
Compara los pisos de ahora con los de la última vez y, si hay NUEVOS,
manda un email a Paula. Guarda el estado en data/seen.json.

Config por variables de entorno (se ponen como "secrets" en GitHub):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS   -> cuenta que envía
  MAIL_TO   (por defecto paula@studioakama.com)
  MAIL_FROM (por defecto = SMTP_USER)
  SITE_URL  (link a la página web, opcional, para meterlo en el email)
Si no hay SMTP configurado, solo actualiza el estado (no falla).
"""
import os, json, smtplib, ssl
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def main():
    listings = load("listings.json", [])
    seen = set(load("seen.json", []))
    current = {l["url"] for l in listings}
    new = [l for l in listings if l["url"] not in seen]

    print(f"Pisos totales: {len(listings)} | nuevos desde la última vez: {len(new)}")

    to = os.environ.get("MAIL_TO", "paula@studioakama.com")
    host = os.environ.get("SMTP_HOST")
    if new and host:
        site = os.environ.get("SITE_URL", "")
        rows = "".join(
            f'<tr><td style="padding:8px;border-bottom:1px solid #eee">'
            f'<b>{l["price"]}€</b> · {l.get("rooms") or "?"} hab</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee">{l.get("title","")[:70]}'
            f'<br><small>{l.get("agency","")}</small></td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee">'
            f'<a href="{l["url"]}">Ver piso ↗</a></td></tr>'
            for l in sorted(new, key=lambda x: x["price"]))
        html = (f'<h2>🏠 {len(new)} piso(s) nuevo(s) en Barcelona</h2>'
                f'{"<p><a href=%r>Abrir la página completa</a></p>" % site if site else ""}'
                f'<table style="border-collapse:collapse;font-family:sans-serif">{rows}</table>'
                f'<p style="color:#888;font-size:12px">≤1150€ · 1-3 hab · Barcelona ciudad · larga estancia</p>')
        msg = EmailMessage()
        msg["Subject"] = f"🏠 {len(new)} piso(s) nuevo(s) en Barcelona (≤1150€)"
        msg["From"] = os.environ.get("MAIL_FROM", os.environ["SMTP_USER"])
        msg["To"] = to
        msg.set_content(f"{len(new)} pisos nuevos. Abre la página: {site}")
        msg.add_alternative(html, subtype="html")
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
        print(f"Email enviado a {to} con {len(new)} pisos nuevos.")
    elif new:
        print("(Hay nuevos pero no hay SMTP configurado: no envío email.)")

    # actualizar estado: lo visto pasa a ser lo de ahora (unión para no re-avisar)
    os.makedirs(DATA, exist_ok=True)
    json.dump(sorted(seen | current), open(os.path.join(DATA, "seen.json"), "w"))


if __name__ == "__main__":
    main()
