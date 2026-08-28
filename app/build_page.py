#!/usr/bin/env python3
"""
Genera la página web (web/index.html) a partir de data/listings.json.
Tarjetas con foto, precio, zona, botón copiar mensaje, link, y registro personal
(favorito, ya hablé, descartar, nota). Los pisos que desaparecen de la web quedan
marcados "No disponible" en vez de borrarse. Todo se guarda en el navegador.
"""
import json, os, html, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
WEB = os.path.join(HERE, "web")

MENSAJE = ("Hola, buenos días. Me interesa el piso. "
           "Soy Paula, 34 años, arquitecta con contrato indefinido y sueldo estable "
           "(unos 2.716 € netos/mes). El piso sería para mí sola; no soy fumadora ni "
           "tengo mascotas. Busco "
           "alquiler de larga duración; tengo toda la documentación lista y avalista "
           "si hiciera falta. ¿Sigue disponible? Me encantaría visitarlo cuando os "
           "venga bien. ¡Gracias! Paula · 633 75 81 50 · paulasalvano258@gmail.com")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def card(l):
    price = l.get("price")
    rooms = l.get("rooms")
    title = l.get("title") or "Piso en alquiler"
    agency = l.get("agency", "")
    url = l.get("url", "#")
    img = l.get("img") or ""
    msg = MENSAJE.format(zona=esc(title)[:60], precio=price)
    rooms_txt = f"{rooms} hab" if rooms else "· hab n/d"
    img_html = (f'<img loading="lazy" src="{esc(img)}" alt="" '
                f'onerror="this.style.display=\'none\';this.parentNode.classList.add(\'noimg\')">'
                if img else "")
    return f"""
    <article class="card" data-url="{esc(url)}">
      <button class="like" title="Me gusta">♥</button>
      <button class="hide" title="Quitar de la vista">✕</button>
      <a class="photo" href="{esc(url)}" target="_blank" rel="noopener">{img_html}
        <span class="ph">🏠</span>
        <span class="price">{price}€</span>
      </a>
      <div class="body">
        <span class="gone-badge">⚠️ No disponible en la web</span>
        <h3>{esc(title)[:90]}</h3>
        <div class="meta">{rooms_txt} · <span class="ag">{esc(agency)}</span></div>
        <div class="actions">
          <button class="btn copy" data-msg="{esc(msg)}">📋 Copiar mensaje</button>
          <a class="btn open" href="{esc(url)}" target="_blank" rel="noopener">Abrir piso ↗</a>
        </div>
        <div class="row2">
          <button class="btn state">✅ Ya hablé</button>
          <button class="btn descartar">🗑️ Descartar</button>
        </div>
        <textarea class="nota" placeholder="📝 Tu nota (se guarda sola)..."></textarea>
      </div>
    </article>"""


CSS = """
  :root { --bg:#0f1115; --card:#181b22; --tx:#e8eaed; --mut:#9aa0aa; --acc:#4f9cff; --ok:#33c481; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--tx); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  header { position:sticky; top:0; background:#0f1115ee; backdrop-filter:blur(8px); padding:14px 16px; border-bottom:1px solid #262a33; z-index:5; }
  header h1 { margin:0; font-size:19px; }
  header .sub { color:var(--mut); font-size:13px; margin-top:3px; }
  .filters { display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; }
  .filters button { background:#20242c; color:var(--tx); border:1px solid #2f3541; border-radius:20px; padding:6px 12px; font-size:12px; cursor:pointer; }
  .filters button.on { background:var(--acc); color:#03204a; border-color:var(--acc); font-weight:700; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; padding:16px; max-width:1200px; margin:0 auto; }
  .card { position:relative; background:var(--card); border:1px solid #262a33; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; }
  .photo { position:relative; display:block; height:180px; background:#20242c; text-decoration:none; }
  .photo img { width:100%; height:100%; object-fit:cover; display:block; }
  .photo .ph { position:absolute; inset:0; display:none; align-items:center; justify-content:center; font-size:46px; opacity:.35; }
  .photo.noimg .ph { display:flex; }
  .photo .price { position:absolute; left:10px; bottom:10px; background:var(--ok); color:#062616; font-weight:700; padding:5px 10px; border-radius:8px; font-size:16px; }
  .body { padding:12px; display:flex; flex-direction:column; gap:8px; flex:1; }
  .body h3 { margin:0; font-size:15px; line-height:1.3; }
  .meta { color:var(--mut); font-size:13px; }
  .ag { color:var(--acc); }
  .actions, .row2 { display:flex; gap:8px; }
  .btn { flex:1; text-align:center; padding:10px; border-radius:9px; border:0; font-size:13px; font-weight:600; cursor:pointer; text-decoration:none; }
  .copy { background:#2a2f3a; color:var(--tx); }
  .copy.copied { background:var(--ok); color:#062616; }
  .open { background:var(--acc); color:#03204a; }
  .state { background:#2a2f3a; color:var(--mut); }
  .descartar { background:#2a2f3a; color:var(--mut); }
  .nota { width:100%; background:#0f1115; color:var(--tx); border:1px solid #2f3541; border-radius:8px; padding:7px; font-size:12px; resize:vertical; min-height:34px; font-family:inherit; }
  .like, .hide { position:absolute; top:8px; width:32px; height:32px; border:0; border-radius:50%; background:#0f1115cc; color:#fff; font-size:16px; cursor:pointer; z-index:2; line-height:1; display:flex; align-items:center; justify-content:center; }
  .like { right:46px; } .hide { right:8px; }
  .card.liked .like { background:#ff2d55; }
  .card.done .state { background:var(--ok); color:#062616; }
  .card.descartado { opacity:.45; }
  .card.descartado .descartar { background:#e5484d; color:#fff; }
  .gone-badge { display:none; background:#5a2530; color:#ffb4c0; font-size:11px; font-weight:700; padding:3px 8px; border-radius:6px; width:fit-content; }
  .card.gone .gone-badge { display:inline-block; }
  .card.gone { border-color:#5a2530; }
  .card.gone .photo { opacity:.6; }
  footer { color:var(--mut); text-align:center; padding:24px; font-size:12px; }
  .empty { text-align:center; color:var(--mut); padding:60px 20px; }
"""

# JavaScript en texto plano (NO f-string) -> sin líos de llaves
SCRIPT = r"""
const K = {liked:'pisos_liked', done:'pisos_done', hidden:'pisos_hidden', desc:'pisos_desc'};
const loadSet = k => new Set(JSON.parse(localStorage.getItem(k) || '[]'));
const saveSet = (k,s) => localStorage.setItem(k, JSON.stringify([...s]));
const loadObj = k => JSON.parse(localStorage.getItem(k) || '{}');
const saveObj = (k,o) => localStorage.setItem(k, JSON.stringify(o));
let liked=loadSet(K.liked), done=loadSet(K.done), hidden=loadSet(K.hidden), desc=loadSet(K.desc);
let notes = loadObj('pisos_notes');
let saved = loadObj('pisos_saved');
let onlyFav=false, hideDone=false, hideDesc=false;

const grid = document.querySelector('.grid');

// 1) Inyectar los que YA no están en la web pero tenés guardados (registro)
if (grid) {
  const current = new Set([...document.querySelectorAll('.card')].map(c => c.dataset.url));
  Object.keys(saved).forEach(url => {
    if (!current.has(url)) {
      const tmp = document.createElement('div');
      tmp.innerHTML = saved[url];
      const c = tmp.firstElementChild;
      if (c) { c.classList.add('gone'); grid.appendChild(c); }
    }
  });
}

function snapshot(card){
  const cl = card.cloneNode(true);
  cl.classList.remove('gone','liked','done','descartado');
  const t = cl.querySelector('.nota'); if (t) t.value = '';
  saved[card.dataset.url] = cl.outerHTML;
  saveObj('pisos_saved', saved);
}

function applyCard(card){
  const u = card.dataset.url;
  card.classList.toggle('liked', liked.has(u));
  card.classList.toggle('done', done.has(u));
  card.classList.toggle('descartado', desc.has(u));
  const st = card.querySelector('.state'); if (st) st.textContent = done.has(u) ? '✔ Ya hablé' : '✅ Ya hablé';
  const db = card.querySelector('.descartar'); if (db) db.textContent = desc.has(u) ? '♻️ Recuperar' : '🗑️ Descartar';
  const na = card.querySelector('.nota'); if (na && notes[u] !== undefined && na.value !== notes[u]) na.value = notes[u];
  let show = !hidden.has(u);
  if (onlyFav && !liked.has(u)) show = false;
  if (hideDone && done.has(u)) show = false;
  if (hideDesc && desc.has(u)) show = false;
  card.style.display = show ? '' : 'none';
}
function applyAll(){ document.querySelectorAll('.card').forEach(applyCard); }

document.querySelectorAll('.card').forEach(card => {
  const u = card.dataset.url;
  const like = card.querySelector('.like');
  const hide = card.querySelector('.hide');
  const state = card.querySelector('.state');
  const dsc = card.querySelector('.descartar');
  const nota = card.querySelector('.nota');
  const copy = card.querySelector('.copy');
  if (like) like.addEventListener('click', e => { e.preventDefault(); liked.has(u)?liked.delete(u):liked.add(u); saveSet(K.liked,liked); snapshot(card); applyCard(card); });
  if (hide) hide.addEventListener('click', e => { e.preventDefault(); hidden.add(u); saveSet(K.hidden,hidden); applyCard(card); });
  if (state) state.addEventListener('click', e => { e.preventDefault(); done.has(u)?done.delete(u):done.add(u); saveSet(K.done,done); snapshot(card); applyCard(card); });
  if (dsc) dsc.addEventListener('click', e => { e.preventDefault(); desc.has(u)?desc.delete(u):desc.add(u); saveSet(K.desc,desc); snapshot(card); applyCard(card); });
  if (nota) nota.addEventListener('input', () => { notes[u] = nota.value; saveObj('pisos_notes', notes); snapshot(card); });
  if (copy) copy.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(copy.dataset.msg);
      copy.textContent='✓ Copiado'; copy.classList.add('copied');
      setTimeout(()=>{ copy.textContent='📋 Copiar mensaje'; copy.classList.remove('copied'); }, 1800);
    } catch(e) { alert(copy.dataset.msg); }
  });
});

const ff = document.getElementById('f-fav');
const fd = document.getElementById('f-done');
const fx = document.getElementById('f-desc');
if (ff) ff.addEventListener('click', () => { onlyFav=!onlyFav; ff.classList.toggle('on',onlyFav); applyAll(); });
if (fd) fd.addEventListener('click', () => { hideDone=!hideDone; fd.classList.toggle('on',hideDone); applyAll(); });
if (fx) fx.addEventListener('click', () => { hideDesc=!hideDesc; fx.classList.toggle('on',hideDesc); applyAll(); });

function relTime(){
  const m = Math.max(0, Math.round((Date.now() - GEN_TS)/60000));
  const el = document.getElementById('upd');
  if (el) el.textContent = m < 1 ? 'recién' : ('hace ' + m + ' min');
}
relTime(); setInterval(relTime, 30000);
setTimeout(() => location.reload(), 240000);
applyAll();
"""


def build():
    path = os.path.join(DATA, "listings.json")
    listings = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    ts = int(time.time())
    cards = "\n".join(card(l) for l in listings)
    n = len(listings)
    agencies = len({l.get("agency") for l in listings})
    body = (f'<div class="grid">{cards}</div>' if n else
            '<div class="empty">Aún no hay pisos que cumplan tus criterios. El vigilante seguirá revisando.</div>')
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Pisos BCN · Paula</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>🏠 Pisos en alquiler · Barcelona</h1>
  <div class="sub">{n} pisos · {agencies} inmobiliarias · ≤1200€ · 1-3 hab · actualizado <b id="upd">recién</b></div>
  <div class="filters">
    <button id="f-fav">❤️ Solo favoritos</button>
    <button id="f-done">🙈 Ocultar los que ya hablé</button>
    <button id="f-desc">🗑️ Ocultar descartados</button>
  </div>
</header>
{body}
<footer>Motor propio · revisa +150 inmobiliarias de Barcelona · hecho para Paula</footer>
<script>const GEN_TS={ts}*1000;</script>
<script>{SCRIPT}</script>
</body>
</html>"""
    os.makedirs(WEB, exist_ok=True)
    open(os.path.join(WEB, "index.html"), "w", encoding="utf-8").write(doc)
    print(f"Página generada ({n} pisos, {agencies} inmobiliarias)")


if __name__ == "__main__":
    build()
