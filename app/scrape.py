#!/usr/bin/env python3
"""
Lector genérico de pisos en alquiler para las webs de inmobiliarias de Barcelona.

Idea: no escribimos un parser por web. Para cada inmobiliaria:
  1) Buscamos su página de "alquiler / lloguer".
  2) Detectamos los pisos por el patrón repetido: bloque con PRECIO (€) + LINK + FOTO.
  3) Extraemos precio, título/zona, habitaciones, link y foto.
  4) Filtramos por precio y habitaciones según los criterios de Paula.

Las webs se leen de ../inmobiliarias.md (todas las URLs https que haya ahí).
Cuando Paula añade una inmobiliaria a esa lista, entra sola.
"""
import re, json, sys, time, html, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
LISTA_MD = os.path.join(ROOT, "inmobiliarias.md")

# ---------- Criterios de Paula ----------
MAX_PRICE = 1100        # tope pedido por Paula (ideal <=1000)
MIN_ROOMS = 1           # pisos de 1, 2 o 3 dormitorios
MAX_ROOMS = 3
MIN_PRICE = 350         # por debajo suele ser habitación/local/error
# Solo larga estancia: fuera temporal/turístico/temporada
TEMPORAL = ["temporal", "temporada", "vacacional", "turíst", "turist", "coliving",
            "co-living", "corta estancia", "curta estada", "por noches", "/noche",
            "short-term", "short term", "airbnb", "estancia mínima", "estada mínima",
            "meses máximo", "mesos màxim", "díes", "days", "monthly"]
# Zonas: acepta todo Barcelona salvo estas
ZONAS_EXCLUIDAS = ["barceloneta"]

# Portales: NO queremos que un piso enlace a Idealista y compañía (Paula ya los tiene)
# Portales que bloquean o no queremos como destino (Paula ya los tiene / bloquean robot).
# OJO: pisos.com NO está aquí: es una FUENTE permitida (ver PORTAL_SOURCES).
PORTALS = ["idealista", "fotocasa", "habitaclia", "enalquiler",
           "yaencontre", "spainhouses", "milanuncios", "wallapop", "badi.com",
           "spotahome", "housinganywhere", "tucasa", "trovimap", "nestpick", "kyero",
           "vibbo", "habitaclia.com", "fotocasa.es"]
# Portales que SÍ podemos leer con navegador real -> fuente extra.
# (nombre, url_base_filtrada_por_precio, nº de páginas a recorrer)
PORTAL_SOURCES = [
    ("pisos.com", "https://www.pisos.com/alquiler/pisos-barcelona_capital/hasta-1200-euros/", 4),
    # Calvet NO va aquí: su buscador solo lista "temporada" y oculta la larga
    # estancia. Se lee aparte, por ficha de ref -> ver scrape_calvet().
]

# ---------- Calvet: lectura por ficha de ref ----------
# Su buscador de alquiler solo muestra pisos de TEMPORADA y oculta los de larga
# estancia (que sí existen, con ref más alta). Los descubrimos abriendo sus fichas
# por número de ref alrededor del "techo" conocido, que se auto-ajusta solo: no
# hace falta saber ningún número, el robot sigue los pisos nuevos aunque cambien.
CALVET_HOST = "https://inmobiliaria.calvetpremium.com"
CALVET_DETAIL = CALVET_HOST + "/es/alquiler-pisos-pisos/en-barcelona-barcelona//ref-%d"
CALVET_CEILING_FILE = os.path.join(DATA, "calvet_ceiling.json")
CALVET_DEFAULT_CEILING = 4115   # suelo de arranque; sube solo con el tiempo

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
           "Accept-Language": "es-ES,es;q=0.9,ca;q=0.8"}

# URLs de listado de alquiler ya descubiertas (van directas, sin adivinar)
OVERRIDES = {
    "www.bunikhome.com": "https://www.bunikhome.com/buscar.php?p=&o=Alquiler",
    "finquesmartell.com": "https://finquesmartell.com/inmuebles",
    "www.finquesfeliu.es": "https://www.finquesfeliu.es/es/buscador/inter",
    "www.fincasblanco.com": "https://www.fincasblanco.com/es/pisos?accion_nombre=alquilar",
    "www.equinoxuh.com": "https://www.equinoxuh.com/es/alquiler/pisos/cataluna/barcelona",
    "www.finquesmartinez.com": "https://www.finquesmartinez.com/es/alquiler-de-pisos-en-barcelona",
    "casablau.net": "https://casablau.net/alquiler/pisos-en-alquiler",
    "barnapiso.com": "https://barnapiso.com/es/propiedades-disponibles-barcelona/",
    "www.rentmar.es": "https://www.rentmar.es/?action=epl_search&post_type=rental&instance_id=1&form_tab=2",
    "toysanfinques.com": "https://toysanfinques.com/es/inmuebles/?transaction_type=lloguer&property__type=property",
    "www.vivalco.com": "https://www.vivalco.com/properties-for-rent/",
}
# Rutas típicas donde las inmobiliarias esconden el listado de alquiler
PATH_GUESSES = ["/alquiler", "/es/alquiler", "/lloguer", "/ca/lloguer", "/inmuebles",
                "/es/inmuebles", "/propiedades", "/viviendas", "/pisos", "/alquileres",
                "/alquiler-de-viviendas", "/inmuebles-en-alquiler", "/buscar", "/obra"]
# Ciudades/pueblos que NO son Barcelona ciudad -> descartar (provincia + resto de España)
OTHER_CITIES = ["terrassa", "sabadell", "vigo", "badalona", "hospitalet", "mataró",
                "mataro", "granollers", "sant cugat", "sitges", "castelldefels", "gavà",
                "gava", "cornellà", "cornella", "esplugues", "mollet", "rubí", "rubi",
                "manresa", " vic", "reus", "tarragona", "girona", "lleida", "montgat",
                "premià", "premia", "vilanova", "igualada", "martorell", "sant just",
                "sant boi", "viladecans", "masnou", "cerdanya", "queixans", "fontanals",
                "sant adrià", "santa coloma", "ripollet", "cerdanyola", "barberà",
                "cáceres", "caceres", "madrid", "valencia", "valència", "sevilla",
                "málaga", "malaga", "zaragoza", "bilbao", "coruña", "coruna", "murcia",
                "alicante", "alacant", "pamplona", "valladolid", "santander", "gijón",
                "gijon", "oviedo", "vitoria", "logroño", "logrono", "salamanca", "cádiz",
                "cadiz", "huelva", "córdoba", "cordoba", "granada", "almería", "almeria",
                "castelldefels", "el prat", "prat de llobregat", "sant joan despí",
                "sant joan despi", "molins de rei", "sant feliu", "el masnou", "vilassar",
                "sant vicenç", "pineda", "calella", "blanes", "lloret", "tossa", "salou",
                "cambrils", "figueres", "olot", "banyoles", "palafrugell", "roses",
                "plasencia", "extremadura", "cáceres", "toledo", "albacete", "badajoz",
                "león", "leon", "burgos", "palencia", "soria", "segovia", "ávila",
                "avila", "cuenca", "guadalajara", "jaén", "jaen", "ourense", "lugo",
                "pontevedra", "ferrol", "santiago", "donostia", "getxo", "irun"]
# Señales de que SÍ es Barcelona ciudad (barrios/distritos)
BCN_HOODS = ["eixample", "gràcia", "gracia", "sants", "poblenou", "poble nou", "clot",
             "sant antoni", "raval", "gòtic", "gotic", "born", "ribera", "barceloneta",
             "sarrià", "sarria", "sant gervasi", "horta", "guinardó", "guinardo",
             "nou barris", "sant andreu", "les corts", "poble sec", "vallcarca",
             "camp de l'arpa", "camp de l arpa", "fort pienc", "sagrada família",
             "sagrada familia", "el carmel", "la salut", "vall d'hebron", "montjuïc",
             "hostafrancs", "la bordeta", "sant martí", "sant marti", "diagonal mar",
             "vila de gràcia", "camp d'en grassot", "la sagrera", "navas", "congrés",
             "bon pastor", "el bon pastor", "trinitat", "baró de viver", "vallbona",
             "verdum", "prosperitat", "porta", "turó de la peira", "can baró"]
# Palabras que indican enlace a la página de alquiler
RENT_HINTS = ["alquiler", "lloguer", "llogar", "alquileres", "lloguers", "rent"]
# Palabras que descartan (no es vivienda residencial)
BAD_WORDS = ["oficina", "local", "nave", "parking", "plaza de aparcamiento", "comercial",
             "traster", "trastero", "solar", "despacho", "aparcament", "garaje", "garatge",
             "despatx", "oficines", "locales", "nau industrial", "plaza de garaje"]
# Palabras de artículos/blog/noticias -> NO son un piso (se colaban con precio suelto)
NEWS_WORDS = ["ley de vivienda", "ley-vivienda", "nueva ley", "nueva-ley", "deduccion",
              "deducción", "autonómica", "autonomica", "/blog", "/noticia", "/actualidad",
              "/consejos", "/guia", "/guía", "claves de", "irpf", "requisitos para",
              "cómo declarar", "como declarar", "qué es", "diferencia entre", "index-of-post",
              "impuesto", "fianza del", "reforma de la ley", "boletín", "boletin"]
# Señal de que SÍ es vivienda (si no aparece ninguna y no hay dormitorios -> fuera)
RESIDENCIAL = ["piso", "pis ", "pis,", "pis.", "estudio", "estudi", "ático", "àtic", "atic",
               "apartament", "apartamento", "vivienda", "habitatge", "dúplex", "duplex",
               "loft", "casa", "chalet", "torre"]

PRICE_RE = re.compile(r'(\d{1,3}(?:[.\s]\d{3})|\d{3,4})\s*€|€\s*(\d{1,3}(?:[.\s]\d{3})|\d{3,4})')
ROOMS_RE = re.compile(r'(\d+)\s*(?:hab|habitaci|dorm|quart|bedroom|dormitori)', re.I)


def get(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


def parse_price(text):
    m = PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group(1) or m.group(2)
    raw = raw.replace(".", "").replace(" ", "")
    try:
        return int(raw)
    except ValueError:
        return None


def find_rent_links(base_url, home_html):
    """Devuelve URLs candidatas a la página de alquiler encontradas en la home."""
    soup = BeautifulSoup(home_html, "lxml")
    cands = []
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").strip().lower()
        href = a["href"].lower()
        if "venta" in href or "venda" in href or "compra" in href:
            continue
        if any(h in txt for h in RENT_HINTS) or any(h in href for h in RENT_HINTS):
            full = urljoin(base_url, a["href"])
            pri = 0 if ("alquiler" in href or "lloguer" in href) else 1
            cands.append((pri, full))
    cands.sort()
    # sin duplicados, manteniendo orden de prioridad
    seen, out = set(), []
    for _, u in cands:
        if u not in seen:
            seen.add(u); out.append(u)
    return out[:4]


# Textos de navegación/banner que NO son un piso
NOISE = ["saltar al contenido", "galería", "galeria", "menú", "menu", "listado",
         "buscar", "contacto", "contacte", "cookie", "más info", "mas info", "regalo",
         "leer más", "llegir més", "ver más", "veure més", "siguiente", "anterior",
         "política", "aviso legal", "newsletter", "suscríb", "iniciar sesión", "acceder",
         "quiénes somos", "qui som", "nosotros", "blog", "compartir", "ampliar",
         "dibuja", "dinos", "lo que buscas", "tu zona", "alertas", "guardar búsqueda"]
GENERIC_TITLES = {"alquiler", "lloguer", "alquilar", "llogar", "piso", "pis",
                  "vivienda", "inmueble", "propiedad", "alquiler en", "en alquiler"}
# La URL de detalle debe parecer una ficha de inmueble
DETAIL_HINTS = ["inmoble", "immoble", "propiedad", "propietat", "inmueble", "vivienda",
                "habitatge", "piso", "pis-", "ficha", "detalle", "detall", "property",
                "ref", "alquiler", "lloguer", "id=", "-id-", "obra", "/p/", "referencia"]


# Últimos segmentos que indican LISTADO/categoría (no una ficha concreta)
LISTING_SEGS = {"listado", "listing", "buscar", "search", "resultados", "results",
                "alquiler", "lloguer", "alquileres", "propiedades", "propietats",
                "inmuebles", "immobles", "viviendas", "habitatges", "pisos", "obra",
                "properties", "rent", "page", "pagina", "categoria", "inmueble",
                "propiedad", "index", "home", "es", "ca", "en"}


def looks_like_detail(url, page_url):
    u = url.lower().split("#")[0].split("?")[0].rstrip("/")
    if u == page_url.lower().split("?")[0].rstrip("/"):
        return False
    if u.startswith(("mailto:", "tel:", "javascript:", "#")):
        return False
    if re.search(r"\.(jpg|jpeg|png|webp|gif|pdf|zip)$", u):   # enlace a imagen/archivo -> no
        return False
    segs = [s for s in urlparse(u).path.split("/") if s]
    if not segs:
        return False
    last = segs[-1]
    if last in LISTING_SEGS:            # termina en una página de listado -> no
        return False
    tail = "/".join(segs[-2:])
    has_id = bool(re.search(r"\d{3,}", tail))          # ref/id de inmueble
    words = [w for w in re.split(r"[-_]", last) if len(w) > 1]
    long_slug = len(words) >= 3                          # slug tipo "piso-alquiler-gracia-.."
    if any(h in u for h in DETAIL_HINTS) and (has_id or long_slug):
        return True
    return len(segs) >= 2 and has_id


def is_room(blob):
    """True si el anuncio es una HABITACIÓN (no un piso entero)."""
    # 'habitaciones' en plural suele ser un piso (ej: '3 habitaciones')
    if ("habitaciones" in blob or "habitacions" in blob) and "compart" not in blob:
        return False
    keys = ["piso compartido", "pis compartit", "compartir piso", "habitación en",
            "habitacion en", "habitació en", "room in", "alquiler de habitación",
            "lloguer d'habitació", "se alquila habitación", "es lloga habitació",
            "habitación con", "habitacion con"]
    return any(k in blob for k in keys)


IMG_ATTRS = ["data-src", "data-lazy-src", "data-original", "data-echo", "data-bg",
             "data-flickity-lazyload", "data-lazy", "data-srcset", "src", "srcset"]


def get_image(block, page_url):
    """Saca la mejor URL de imagen del bloque (cubre lazy-load y srcset)."""
    for im in block.find_all("img"):
        for attr in IMG_ATTRS:
            v = im.get(attr)
            if v and "data:image" not in v:
                v = v.split(",")[0].strip().split(" ")[0]   # srcset -> primera
                if v.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) or "/" in v:
                    return urljoin(page_url, v)
    # <source srcset> dentro de <picture>
    src = block.find("source")
    if src and src.get("srcset"):
        return urljoin(page_url, src["srcset"].split(",")[0].strip().split(" ")[0])
    # background-image en estilos inline
    m = re.search(r'background-image\s*:\s*url\(["\']?([^"\')]+)', str(block))
    if m:
        return urljoin(page_url, m.group(1))
    return None


def title_from_url(url):
    """Cuando el título es un número, saca algo legible del slug de la URL."""
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r'^\d+[_-]', '', slug)          # quita id inicial
    slug = re.sub(r'[-_]ref[-_].*$', '', slug, flags=re.I)
    slug = slug.replace("-", " ").replace("_", " ").strip()
    return slug[:1].upper() + slug[1:] if slug else ""


def extract_listings(page_url, page_html):
    """Extractor genérico: busca bloques con precio + link de ficha + (foto)."""
    soup = BeautifulSoup(page_html, "lxml")
    host = urlparse(page_url).netloc
    found = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        if urlparse(href).netloc and urlparse(href).netloc != host:
            continue
        if not looks_like_detail(href, page_url):
            continue
        # contenedor del anuncio: subimos hasta 6 niveles y elegimos el ancestro
        # más cercano que tenga una imagen (así capturamos la foto del card);
        # si ninguno tiene, usamos el 3º nivel como antes.
        parents = []
        b = a
        for _ in range(6):
            if b.parent is None:
                break
            b = b.parent
            parents.append(b)
        # ancestro más cercano con imagen Y precio (evita cards donde el enlace
        # envuelve solo la foto); si no hay, caemos al de imagen y luego al 3º nivel
        block = next((pp for pp in parents
                      if pp.find("img") is not None and parse_price(pp.get_text(" ", strip=True))),
                     next((pp for pp in parents if pp.find("img") is not None),
                          parents[min(2, len(parents) - 1)] if parents else a))
        text = " ".join(block.get_text(" ", strip=True).split())
        price = parse_price(text)
        if not price:
            continue
        # descartar RESERVAT/reservado/alquilado (badge de estado en la card;
        # a veces va en un atributo lazy de la imagen, así que miramos todo el HTML)
        bl = text.lower() + " " + str(block).lower()
        if re.search(r'reservat|reservad[oa]|llogad[ao]|alquilad[oa]', bl) \
                and "derecho" not in bl and "rights" not in bl:
            continue
        img = get_image(block, page_url)
        rooms_m = ROOMS_RE.search(text)
        rooms = int(rooms_m.group(1)) if rooms_m else None
        if rooms is not None and not (1 <= rooms <= 8):
            rooms = None      # descartamos números absurdos (superficies, etc.)
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if not title or len(title) < 5:
            h = block.find(["h1", "h2", "h3", "h4"])
            title = h.get_text(" ", strip=True) if h else ""
        if not title or title.replace(" ", "").isdigit() or len(title) < 5:
            title = title_from_url(href) or title      # slug legible si es un número
        tl = title.lower().strip()
        if not title or tl in GENERIC_TITLES or any(n in tl for n in NOISE):
            continue
        key = href.split("#")[0]
        blob = (title + " " + text + " " + href).lower()
        kind = "habitacion" if is_room(blob) else "piso"
        dedup = (price, title[:45].lower())
        score = (2 if img else 0) + (1 if rooms else 0) + (1 if len(title) > 12 else 0)
        prev = found.get(key)
        if prev is None or score > prev["_score"]:
            found[key] = {"url": key, "price": price, "rooms": rooms, "kind": kind,
                          "title": title[:120], "img": img, "text": text[:180],
                          "_dedup": dedup, "_score": score}
    # segundo dedup: mismo precio+título aunque cambie la URL
    by_dedup = {}
    for v in found.values():
        d = v["_dedup"]
        if d not in by_dedup or v["_score"] > by_dedup[d]["_score"]:
            by_dedup[d] = v
    res = list(by_dedup.values())
    for v in res:
        v.pop("_dedup", None)
    return res[:30]


def passes_filters(item):
    p = item["price"]
    if p is None or p < MIN_PRICE or p > MAX_PRICE:
        return False
    if not item.get("img"):          # sin foto no lo mostramos (se veía roto)
        return False
    url_l = item.get("url", "").lower()
    if any(p in url_l for p in PORTALS):     # nada de enlaces a Idealista/Fotocasa/etc.
        return False
    if any(s in url_l for s in ["venta", "venda", "vender", "compra", "obra-nueva",
                                "quieres-alquilar", "vender-tu-piso"]):
        return False                 # es venta o página-anzuelo, no un alquiler
    low = (item["title"] + " " + item.get("text", "") + " " + item.get("url", "")).lower()
    if any(b in low for b in BAD_WORDS):
        return False
    # artículos de blog/noticias (no son pisos): título-pregunta o slug informativo
    if item["title"].strip()[:1] in ("¿", "¡", "?"):
        return False
    if any(w in low for w in NEWS_WORDS):
        return False
    if any(z in low for z in ZONAS_EXCLUIDAS):
        return False
    # SOLO Barcelona ciudad: descartar cualquier otro pueblo/ciudad...
    if any(c in low for c in OTHER_CITIES):
        return False
    # ...y exigir señal explícita de Barcelona ciudad (la palabra o un barrio)
    if "barcelona" not in low and not any(n in low for n in BCN_HOODS):
        return False
    if any(t in low for t in TEMPORAL):          # solo larga estancia
        return False
    if item.get("kind") == "habitacion":         # nada de habitación suelta / compartir
        return False
    r = item.get("rooms")
    if r is not None and not (MIN_ROOMS <= r <= MAX_ROOMS):   # pisos de 1 a 3 dormitorios
        return False
    # exigir señal de vivienda: si no dice piso/estudio/etc. y no tiene dormitorios,
    # es ambiguo (suele ser local/oficina de una finca) -> fuera
    if r is None and not any(w in low for w in RESIDENCIAL):
        return False
    return True


def scrape_site(name, base_url, fetch=None):
    """fetch(url)->html. Por defecto lector rápido (requests); en modo headless
    se le pasa un fetch que ejecuta JavaScript (navegador real)."""
    if fetch is None:
        fetch = lambda u: get(u).text
    out = {"name": name, "base": base_url, "ok": False, "listings": [], "error": None}
    host = urlparse(base_url).netloc
    try:
        # 1) construir lista de páginas candidatas donde puede estar el listado
        candidates = []
        if host in OVERRIDES:
            candidates.append(OVERRIDES[host])
        try:
            candidates += find_rent_links(base_url, fetch(base_url))
        except Exception:
            pass
        candidates += [urljoin(base_url, p) for p in PATH_GUESSES]
        candidates.append(base_url)
        seen, cand = set(), []
        for c in candidates:
            if c in seen:
                continue
            if any(p in urlparse(c).netloc for p in PORTALS):   # no rastrear portales
                continue
            seen.add(c); cand.append(c)
        cand = cand[:6]
        # 2) probar cada candidata, quedarnos con la que da más pisos válidos
        best = {"good": [], "url": base_url, "n_raw": 0}
        for url in cand:
            try:
                page_html = fetch(url)
            except Exception:
                continue
            items = extract_listings(url, page_html)
            good = [i for i in items if passes_filters(i)]
            if len(good) > len(best["good"]):
                best = {"good": good, "url": url, "n_raw": len(items)}
            if len(good) >= 3:
                break
        for g in best["good"]:
            g["agency"] = name
            g["rent_url"] = best["url"]
            g.pop("_score", None)
        out.update(ok=True, listings=best["good"], rent_url=best["url"], n_raw=best["n_raw"])
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


async def _block(route):
    if route.request.resource_type in ("image", "font", "media"):
        await route.abort()
    else:
        await route.continue_()


async def _fetch_page(page, url):
    """Carga una URL con navegador real. A prueba de cuelgues (tiempos cortos)."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
    except Exception:
        pass
    try:
        await page.wait_for_timeout(1000)
        for _ in range(3):          # scroll para disparar la carga lazy de fotos
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(200)
        return await page.content()
    except Exception:
        return ""


async def _scrape_site_async(browser, name, base_url, block_imgs=True):
    out = {"name": name, "base": base_url, "ok": False, "listings": [], "error": None}
    host = urlparse(base_url).netloc
    ctx = None
    try:
        ctx = await browser.new_context(user_agent=HEADERS["User-Agent"], locale="es-ES",
                                        viewport={"width": 1280, "height": 900})
        if block_imgs:
            await ctx.route("**/*", _block)
        page = await ctx.new_page()
        page.set_default_timeout(12000)
        candidates = []
        if host in OVERRIDES:
            candidates.append(OVERRIDES[host])
        home = await _fetch_page(page, base_url)
        if home:
            candidates += find_rent_links(base_url, home)
        candidates += [urljoin(base_url, p) for p in PATH_GUESSES]
        candidates.append(base_url)
        seen, cand = set(), []
        for c in candidates:
            if c in seen or any(p in urlparse(c).netloc for p in PORTALS):
                continue
            seen.add(c); cand.append(c)
        best = {"good": [], "url": base_url}
        for url in cand[:6]:
            html = await _fetch_page(page, url)
            if not html:
                continue
            good = [i for i in extract_listings(url, html) if passes_filters(i)]
            if len(good) > len(best["good"]):
                best = {"good": good, "url": url}
            if len(good) >= 3:
                break
        for g in best["good"]:
            g["agency"] = name; g["rent_url"] = best["url"]; g.pop("_score", None)
        out.update(ok=True, listings=best["good"], rent_url=best["url"])
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    finally:
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
    return out


async def _scrape_portal_async(browser, pname, purl, npages):
    good = []
    ctx = None
    try:
        ctx = await browser.new_context(user_agent=HEADERS["User-Agent"], locale="es-ES",
                                        viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()      # portales: NO bloqueamos imágenes (foto en src)
        page.set_default_timeout(12000)
        for k in range(1, npages + 1):
            page_url = purl if k == 1 else purl.rstrip("/") + f"/{k}/"
            html = await _fetch_page(page, page_url)
            if not html:
                continue
            for it in extract_listings(page_url, html):
                if passes_filters(it):
                    it["agency"] = pname; it["rent_url"] = purl; it.pop("_score", None)
                    good.append(it)
    finally:
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
    return {"name": pname, "base": f"https://{urlparse(purl).netloc}/portal-{pname}",
            "ok": True, "listings": good, "error": None}


async def _headless_async(sites, portals, concurrency):
    from playwright.async_api import async_playwright
    import asyncio
    sem = asyncio.Semaphore(concurrency)

    async def guarded(coro_func, *a):
        async with sem:
            # tope duro por tarea: si el navegador se cae, NO se cuelga eternamente
            try:
                return await asyncio.wait_for(coro_func(*a), timeout=60)
            except Exception as e:
                return {"name": a[1] if len(a) > 1 else "?", "base": "", "ok": False,
                        "listings": [], "error": f"timeout/err: {type(e).__name__}"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [guarded(_scrape_site_async, browser, n, u) for n, u in sites]
        tasks += [guarded(_scrape_portal_async, browser, pn, pu, npg) for pn, pu, npg in portals]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        try:
            await browser.close()
        except Exception:
            pass
    return [r for r in results if isinstance(r, dict)]


def headless_pass(sites, portals=None, concurrency=4):
    """Pasada con navegador real (Playwright), EN PARALELO (varias webs a la vez)
    para webs con JavaScript + portales-fuente. Rápido y a prueba de cuelgues."""
    import asyncio
    return asyncio.run(_headless_async(sites, portals or [], concurrency))


def _calvet_ref_info(ref):
    """Abre la ficha de un ref de Calvet y devuelve el piso si es alquiler de larga
    estancia en Barcelona. 'blocked' si la web nos frena; None si no existe/no sirve."""
    try:
        h = get(CALVET_DETAIL % ref, timeout=15).text
    except Exception:
        return None
    if "Acceso temporalmente bloqueado" in h:
        return "blocked"
    if len(h) < 5000 or "TEMPORADA" in h:      # ficha vacía o de temporada -> fuera
        return None
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    if re.search(r"venta:\s*[0-9]", t):        # es de venta, no alquiler
        return None
    pm = re.search(r"alquiler:\s*([0-9][0-9\.]*)", t)
    if not pm:
        return None
    price = int(pm.group(1).replace(".", ""))
    tm = re.search(r'og:title"\s*content="([^"]+)"', h)
    im = re.search(r'og:image"\s*content="([^"]+)"', h)
    rm = re.search(r"Dormitorios\s*([0-9])", t)
    return {"url": CALVET_DETAIL % ref, "price": price,
            "rooms": int(rm.group(1)) if rm else None, "kind": "piso",
            "title": html.unescape((tm.group(1) if tm else "Piso Calvet").strip())[:120],
            "img": im.group(1) if im else "", "text": t[:180], "agency": "Calvet"}


CALVET_CACHE_FILE = os.path.join(DATA, "calvet_cache.json")
CALVET_RESCAN_SECS = 25 * 60      # re-escanear Calvet como mucho cada ~25 min

def _calvet_scan(window_down=30, window_up=10):
    """Lee las fichas de Calvet alrededor del techo conocido (auto-ajustable) y
    devuelve (listings, max_ref_visto). En paralelo suave (3 a la vez)."""
    ceiling = CALVET_DEFAULT_CEILING
    try:
        ceiling = max(ceiling, int(json.load(open(CALVET_CEILING_FILE)).get("ceiling", 0)))
    except Exception:
        pass
    refs = list(range(ceiling + window_up, ceiling - window_down, -1))
    good, max_seen = [], ceiling
    with ThreadPoolExecutor(max_workers=3) as ex:      # suave, no dispara el anti-robot
        for ref, info in zip(refs, ex.map(_calvet_ref_info, refs)):
            if info and info != "blocked":
                max_seen = max(max_seen, ref)
                if passes_filters(info):
                    good.append(info)
    try:
        json.dump({"ceiling": max_seen}, open(CALVET_CEILING_FILE, "w"))
    except Exception:
        pass
    return good, max_seen


def scrape_calvet():
    """Devuelve los alquileres de larga estancia de Calvet. Usa caché: solo re-escanea
    la web cada ~25 min; el resto del tiempo reusa lo último bueno. Así cada pasada
    del robot es rápida (no se pasa de los 5 min) y no martillamos la web de Calvet."""
    cache = {}
    try:
        cache = json.load(open(CALVET_CACHE_FILE))
    except Exception:
        pass
    fresh = (time.time() - cache.get("ts", 0)) < CALVET_RESCAN_SECS
    if fresh and cache.get("listings"):
        good = cache["listings"]
        print(f"  Calvet (caché): {len(good)} pisos", file=sys.stderr)
    else:
        good, _ = _calvet_scan()
        # si el escaneo vino vacío (p.ej. la web nos frenó) pero teníamos caché
        # buena, la conservamos para no dejar la página sin Calvet
        if not good and cache.get("listings"):
            good = cache["listings"]
            print("  Calvet: escaneo vacío, mantengo la caché anterior", file=sys.stderr)
        else:
            try:
                json.dump({"ts": time.time(), "listings": good},
                          open(CALVET_CACHE_FILE, "w"), ensure_ascii=False)
            except Exception:
                pass
        print(f"  Calvet (escaneo): {len(good)} pisos de larga estancia", file=sys.stderr)
    return {"name": "Calvet", "base": CALVET_HOST + "/portal-Calvet",
            "ok": True, "listings": good, "error": None}


def load_sites():
    """Lee todas las URLs https de inmobiliarias.md (excluye directorios madre)."""
    txt = open(LISTA_MD, encoding="utf-8").read()
    skip = ["idealista.com", "borsalloguers", "cafbl.cat", "apibcn.com", "cylex.es",
            "facebook.com", "engelvoelkers.com"]
    sites = {}
    # capturamos "Nombre | https://..." o "[Nombre](url)" y URLs sueltas
    for m in re.finditer(r'\|\s*([^|]+?)\s*\|\s*(https?://[^\s|)]+)', txt):
        name, url = m.group(1).strip().strip("⭐ ").strip(), m.group(2).strip()
        if any(s in url for s in skip):
            continue
        host = urlparse(url).netloc
        if host and host not in sites:
            sites[host] = (name, f"{urlparse(url).scheme}://{host}/")
    return list(sites.values())


def main():
    limit = 0
    do_headless = True
    fast = False        # --fast: NO scan pesado de agencias con navegador (evita caídas
                        # en el Mac); solo clásicas + pisos.com. El scan completo va en la nube.
    for a in sys.argv[1:]:
        if a.isdigit():
            limit = int(a)
        elif a == "--no-headless":
            do_headless = False
        elif a == "--fast":
            fast = True
    sites = load_sites()
    if limit:
        sites = sites[:limit]
    print(f"Leyendo {len(sites)} inmobiliarias (lector rápido)...", file=sys.stderr)
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(scrape_site, n, u): n for n, u in sites}
        for f in as_completed(futs):
            results.append(f.result())
    by_host = {urlparse(r["base"]).netloc: r for r in results}
    # Las webs que quedaron VACÍAS suelen ser de JavaScript -> navegador real
    if do_headless:
        zero = [] if fast else [(r["name"], r["base"]) for r in results if not r["listings"]]
        modo = "solo portales (modo rápido)" if fast else f"{len(zero)} webs + portales"
        print(f"Navegador real: {modo}...", file=sys.stderr)
        try:
            for r in headless_pass(zero, PORTAL_SOURCES):
                if r["listings"]:
                    by_host[urlparse(r["base"]).netloc] = r
        except Exception as e:
            print(f"(navegador real no disponible: {type(e).__name__}: {e})", file=sys.stderr)
    # Calvet aparte: por ficha de ref (su buscador oculta la larga estancia)
    try:
        by_host["calvet-ref"] = scrape_calvet()
    except Exception as e:
        print(f"(Calvet por ficha falló: {type(e).__name__}: {e})", file=sys.stderr)
    results = list(by_host.values())
    all_listings = []
    ok = err = 0
    for r in results:
        if r["ok"]:
            ok += 1
            all_listings.extend(r["listings"])
        else:
            err += 1
    # dedup global por URL
    uniq = {}
    for l in all_listings:
        uniq.setdefault(l["url"], l)
    all_listings = sorted(uniq.values(), key=lambda x: x["price"])
    os.makedirs(DATA, exist_ok=True)
    json.dump(all_listings, open(os.path.join(DATA, "listings.json"), "w"),
              ensure_ascii=False, indent=2)
    print(f"\nWebs OK: {ok} | con error: {err}", file=sys.stderr)
    print(f"Pisos que cumplen filtros: {len(all_listings)}", file=sys.stderr)
    for l in all_listings[:25]:
        print(f"  {l['price']}€  {l.get('rooms') or '?'}h  [{l['agency']}]  {l['title'][:50]}", file=sys.stderr)


if __name__ == "__main__":
    main()
