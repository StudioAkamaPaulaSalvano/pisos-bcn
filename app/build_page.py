#!/usr/bin/env python3
"""
Genera la página web (web/index.html) a partir de data/listings.json.
Tarjetas con foto, precio, zona, botón "copiar mensaje" y link para contactar.
Es un archivo estático -> sirve tal cual en GitHub Pages y se abre en el móvil.
"""
import json, os, html, datetime, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
WEB = os.path.join(HERE, "web")

# --- Tu mensaje (edítalo una vez con tus datos; {zona} y {precio} se rellenan solos) ---
MENSAJE = ("Hola, buenos días. Me interesa mucho el piso de {zona} de {precio}€. "
           "Soy [NOMBRE], con ingresos estables. Seríamos [Nº] personas, no fumadores "
           "y sin mascotas. Puedo aportar nóminas/aval y tengo dossier con la "
           "documentación listo. Puedo ir a verlo hoy o mañana a la hora que os venga "
           "bien. ¿Sigue disponible? Gracias.")


def esc(s):
    return html.escape(s or "", quote=True)


def card(l):
    price = l.get("price")
    rooms = l.get("rooms")
    title = l.get("title") or "Piso en alquiler"
    zona = title
    agency = l.get("agency", "")
    url = l.get("url", "#")
    img = l.get("img") or ""
    msg = MENSAJE.format(zona=esc(zona)[:60], precio=price)
    rooms_txt = f"{rooms} hab" if rooms else "· hab n/d"
    img_html = (f'<img loading="lazy" src="{esc(img)}" alt="" '
                f'onerror="this.style.display=\'none\';this.parentNode.classList.add(\'noimg\')">'
                if img else "")
    return f"""
    <article class="card" data-url="{esc(url)}">
      <button class="like" title="Me gusta" data-url="{esc(url)}">♥</button>
      <button class="hide" title="Quitar de mi lista" data-url="{esc(url)}">✕</button>
      <a class="photo" href="{esc(url)}" target="_blank" rel="noopener">{img_html}
        <span class="ph">🏠</span>
        <span class="price">{price}€</span>
      </a>
      <div class="body">
        <h3>{esc(title)[:90]}</h3>
        <div class="meta">{rooms_txt} · <span class="ag">{esc(agency)}</span></div>
        <div class="actions">
          <button class="btn copy" data-msg="{esc(msg)}">📋 Copiar mensaje</button>
          <a class="btn open" href="{esc(url)}" target="_blank" rel="noopener">Abrir piso ↗</a>
        </div>
        <button class="btn state" data-url="{esc(url)}">✅ Ya hablé</button>
      </div>
    </article>"""


def build():
    path = os.path.join(DATA, "listings.json")
    listings = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    ts = int(time.time())
    cards = "\n".join(card(l) for l in listings)
    n = len(listings)
    agencies = len({l.get("agency") for l in listings})
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Pisos BCN · Paula</title>
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --tx:#e8eaed; --mut:#9aa0aa; --acc:#4f9cff; --ok:#33c481; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--tx); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  header {{ position:sticky; top:0; background:#0f1115ee; backdrop-filter:blur(8px); padding:14px 16px; border-bottom:1px solid #262a33; z-index:5; }}
  header h1 {{ margin:0; font-size:19px; }}
  header .sub {{ color:var(--mut); font-size:13px; margin-top:3px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; padding:16px; max-width:1200px; margin:0 auto; }}
  .card {{ background:var(--card); border:1px solid #262a33; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; }}
  .photo {{ position:relative; display:block; height:180px; background:#20242c; text-decoration:none; }}
  .photo img {{ width:100%; height:100%; object-fit:cover; display:block; }}
  .photo .ph {{ position:absolute; inset:0; display:none; align-items:center; justify-content:center; font-size:46px; opacity:.35; }}
  .photo.noimg .ph {{ display:flex; }}
  .photo .price {{ position:absolute; left:10px; bottom:10px; background:var(--ok); color:#062616; font-weight:700; padding:5px 10px; border-radius:8px; font-size:16px; }}
  .body {{ padding:12px; display:flex; flex-direction:column; gap:8px; flex:1; }}
  .body h3 {{ margin:0; font-size:15px; line-height:1.3; }}
  .meta {{ color:var(--mut); font-size:13px; }}
  .ag {{ color:var(--acc); }}
  .actions {{ display:flex; gap:8px; margin-top:auto; }}
  .btn {{ flex:1; text-align:center; padding:10px; border-radius:9px; border:0; font-size:13px; font-weight:600; cursor:pointer; text-decoration:none; }}
  .copy {{ background:#2a2f3a; color:var(--tx); }}
  .copy.done {{ background:var(--ok); color:#062616; }}
  .open {{ background:var(--acc); color:#03204a; }}
  footer {{ color:var(--mut); text-align:center; padding:24px; font-size:12px; }}
  .empty {{ text-align:center; color:var(--mut); padding:60px 20px; }}
  .card {{ position:relative; }}
  .like, .hide {{ position:absolute; top:8px; width:32px; height:32px; border:0; border-radius:50%;
     background:#0f1115cc; color:#fff; font-size:16px; cursor:pointer; z-index:2; line-height:1;
     display:flex; align-items:center; justify-content:center; backdrop-filter:blur(3px); }}
  .like {{ right:46px; }}
  .hide {{ right:8px; }}
  .like:hover {{ color:#ff5a7a; }}
  .card.liked .like {{ background:#ff2d55; color:#fff; }}
  .state {{ background:#2a2f3a; color:var(--mut); margin-top:2px; }}
  .card.done {{ opacity:.55; }}
  .card.done .state {{ background:var(--ok); color:#062616; }}
  .filters {{ display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; }}
  .filters button {{ background:#20242c; color:var(--tx); border:1px solid #2f3541; border-radius:20px;
     padding:6px 12px; font-size:12px; cursor:pointer; }}
  .filters button.on {{ background:var(--acc); color:#03204a; border-color:var(--acc); font-weight:700; }}
</style>
</head>
<body>
<header>
  <h1>🏠 Pisos en alquiler · Barcelona</h1>
  <div class="sub">{n} pisos · {agencies} inmobiliarias · ≤1200€ · 1-3 hab · actualizado <b id="upd">recién</b></div>
  <div class="filters">
    <button id="f-fav">❤️ Solo favoritos</button>
    <button id="f-hidedone">🙈 Ocultar los que ya hablé</button>
  </div>
</header>
{'<div class="grid">'+cards+'</div>' if n else '<div class="empty">Aún no hay pisos que cumplan tus criterios. El vigilante seguirá revisando.</div>'}
<footer>Motor propio · revisa +150 inmobiliarias de Barcelona · hecho para Paula</footer>
<script>
const GEN_TS={ts}*1000;
function relTime(){{
  const m=Math.max(0,Math.round((Date.now()-GEN_TS)/60000));
  const el=document.getElementById('upd');
  if(el) el.textContent = m<1 ? 'recién' : ('hace '+m+' min');
}}
relTime(); setInterval(relTime,30000);
setTimeout(()=>location.reload(), 240000);   // se refresca sola cada 4 min

const KEYS={{liked:'pisos_liked',done:'pisos_done',hidden:'pisos_hidden'}};
const load=k=>new Set(JSON.parse(localStorage.getItem(k)||'[]'));
const save=(k,s)=>localStorage.setItem(k,JSON.stringify([...s]));
let liked=load(KEYS.liked), done=load(KEYS.done), hidden=load(KEYS.hidden);
let onlyFav=false, hideDone=false;

function applyCard(card){{
  const u=card.dataset.url;
  card.classList.toggle('liked', liked.has(u));
  card.classList.toggle('done', done.has(u));
  const st=card.querySelector('.state'); if(st) st.textContent = done.has(u)?'✔ Ya hablé':'✅ Ya hablé';
  let show = !hidden.has(u);
  if(onlyFav && !liked.has(u)) show=false;
  if(hideDone && done.has(u)) show=false;
  card.style.display = show?'':'none';
}}
function applyAll(){{ document.querySelectorAll('.card').forEach(applyCard); }}

document.querySelectorAll('.like').forEach(b=>b.addEventListener('click',e=>{{
  e.preventDefault(); const u=b.dataset.url;
  liked.has(u)?liked.delete(u):liked.add(u); save(KEYS.liked,liked);
  applyCard(b.closest('.card'));
}}));
document.querySelectorAll('.hide').forEach(b=>b.addEventListener('click',e=>{{
  e.preventDefault(); const u=b.dataset.url; hidden.add(u); save(KEYS.hidden,hidden);
  b.closest('.card').style.display='none';
}}));
document.querySelectorAll('.state').forEach(b=>b.addEventListener('click',e=>{{
  e.preventDefault(); const u=b.dataset.url;
  done.has(u)?done.delete(u):done.add(u); save(KEYS.done,done);
  applyCard(b.closest('.card'));
}}));
const ff=document.getElementById('f-fav'), fd=document.getElementById('f-hidedone');
ff.addEventListener('click',()=>{{onlyFav=!onlyFav; ff.classList.toggle('on',onlyFav); applyAll();}});
fd.addEventListener('click',()=>{{hideDone=!hideDone; fd.classList.toggle('on',hideDone); applyAll();}});

document.querySelectorAll('.copy').forEach(b => b.addEventListener('click', async () => {{
  try {{ await navigator.clipboard.writeText(b.dataset.msg);
    b.textContent='✓ Copiado'; b.classList.add('done');
    setTimeout(()=>{{b.textContent='📋 Copiar mensaje'; b.classList.remove('done');}}, 1800);
  }} catch(e) {{ alert(b.dataset.msg); }}
}}));
applyAll();
</script>
</body>
</html>"""
    os.makedirs(WEB, exist_ok=True)
    out = os.path.join(WEB, "index.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"Página generada: {out}  ({n} pisos, {agencies} inmobiliarias)")


if __name__ == "__main__":
    build()
