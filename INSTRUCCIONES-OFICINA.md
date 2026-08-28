# 🏠 Buscador de pisos Barcelona — montar en el PC de la oficina (24/7)

> **Para el Claude / la persona de la otra compu:** esto es un buscador propio de
> pisos de alquiler en Barcelona. Ya funciona en la nube (GitHub), pero acá en la
> oficina queremos correrlo **en modo tiempo real** (revisa cada ~1 min, sin
> depender del reloj de GitHub) porque esta compu está **encendida 24 h**.
> Tu tarea: dejarlo corriendo en bucle y que no se pare.

## Qué hace
Cada ~60 s revisa webs de inmobiliarias + pisos.com + Calvet, filtra pisos
**≤1200€, 1-3 dormitorios, Barcelona ciudad, larga estancia**, y arma una página
web con foto + botón "copiar mensaje" + link. La sirve en `http://localhost:8000`.

## Pasos (una sola vez)

### 1) Tener Python 3 (comprobar en terminal)
- `python3 --version`  (o `python --version` en Windows). Si no está, instalar desde python.org.

### 2) Clonar el proyecto
```
git clone https://github.com/StudioAkamaPaulaSalvano/pisos-bcn.git
cd pisos-bcn
```

### 3) Instalar dependencias
**Mac / Linux:**
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```
**Windows (PowerShell):**
```
python -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

### 4) Arrancar el modo tiempo real
```
python realtime.py
```
- Abrí **http://localhost:8000** en el navegador de esta compu.
- Desde el **móvil** (misma wifi): mirá la IP local de esta compu (ej. 192.168.1.40)
  y entrá a **http://192.168.1.40:8000**.

## Que NO se pare (24/7)
- **Lo más simple:** dejar la terminal abierta con `python realtime.py` corriendo.
- **Mac (que no se duerma):** `caffeinate -s python realtime.py`
  o dejar la terminal abierta + Ajustes → Batería → no suspender.
- **Windows:** dejar la ventana abierta; o programarlo con el **Programador de tareas**
  para que arranque al iniciar sesión (acción: `python`, argumentos: ruta a `realtime.py`).

## Opcional
- **Cambiar cada cuánto revisa:** `python realtime.py 30` (cada 30 s).
- **Email de avisos:** definir variables de entorno `SMTP_HOST`, `SMTP_PORT`,
  `SMTP_USER`, `SMTP_PASS`, `MAIL_TO=paula@studioakama.com` antes de correr.
- **Criterios** (precio, zonas, etc.): están arriba de `app/scrape.py`.
- **Añadir inmobiliarias:** pegar su web en `inmobiliarias.md` (entra sola).

## Notas
- Es un proyecto separado; NO tiene nada que ver con la web de Studio Akama.
- La página online sigue viva igual: https://studioakamapaulasalvano.github.io/pisos-bcn/

---
### Prompt corto para pegarle al Claude de la oficina
> "Cloná https://github.com/StudioAkamaPaulaSalvano/pisos-bcn y seguí
> INSTRUCCIONES-OFICINA.md para dejarlo corriendo 24/7 con `python realtime.py`.
> Confirmame la IP local así lo abro desde el móvil."
