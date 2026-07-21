# Deploy — Jarvis

Runbook para dejar el backend en producción. **Monorepo**: cada servicio apunta a su subcarpeta
como raíz, así que un solo repo no afecta la velocidad (cada build empaqueta solo lo suyo).

Topología: **Render** (backend FastAPI, siempre encendido) · **Supabase** (Postgres+pgvector y
Storage del audio) · **Vercel** (frontend, cuando exista `apps/web`).

## 1. Supabase (base de datos + storage)

1. Crea un proyecto en supabase.com. Guarda la contraseña de la base.
2. **Connection string** — usa el **Session pooler** (IPv4), NO la conexión directa. La directa
   (`db.<REF>.supabase.co`) es **solo IPv6** y Render sale por IPv4 → daría `Network is unreachable`.
   En el botón **Connect** (arriba) → **Session pooler** → copia el URI. Se ve así (fíjate: host
   `pooler.supabase.com` y usuario `postgres.<REF>`):
   ```
   postgresql://postgres.<REF>:<PASSWORD>@<REGION>.pooler.supabase.com:5432/postgres
   ```
   Cámbiale el esquema a `+asyncpg` y úsalo como `JARVIS_DATABASE_URL`:
   ```
   postgresql+asyncpg://postgres.<REF>:<PASSWORD>@<REGION>.pooler.supabase.com:5432/postgres
   ```
   - **Session pooler = puerto 5432** (server persistente, prepared statements OK). No uses el
     transaction pooler (6543).
   - El SSL lo exige el código automáticamente para hosts remotos.
   - Si la contraseña trae símbolos (`,` `*` …) y falla, resetéala en Supabase a una alfanumérica.
3. **pgvector**: la migración `0001` corre `CREATE EXTENSION IF NOT EXISTS vector`. Si el rol no
   tuviera permiso, actívala en Database → Extensions → habilita `vector`.
4. **Storage**: crea un bucket llamado `podcasts` y márcalo **público** (Storage → New bucket →
   Public). Ahí se sirve el audio del podcast.
5. Toma dos valores de Project Settings → API:
   - Project URL → `JARVIS_SUPABASE_URL` (ej. `https://<REF>.supabase.co`).
   - `service_role` **secret** → `JARVIS_SUPABASE_SERVICE_KEY` (no la anon key).

## 2. Render (backend)

1. New → **Blueprint** y apunta al repo: Render lee `render.yaml` (servicio Docker con
   `dockerContext: apps/backend`). Alternativa manual: New → Web Service → Docker, y setea
   *Root Directory* = `apps/backend`.
2. Completa las variables marcadas `sync: false`:
   - `JARVIS_GEMINI_API_KEY` (Google AI Studio) — carril inmediato y TTS.
   - `JARVIS_OPENROUTER_API_KEY` — escape para otros modelos (opcional al inicio).
   - `JARVIS_DATABASE_URL` — la de Supabase (paso 1.2).
   - `JARVIS_SUPABASE_URL`, `JARVIS_SUPABASE_SERVICE_KEY` — del paso 1.5.
   - `JARVIS_HERALDO_FEEDS` — feeds RSS separados por coma (opcional).
3. Deploy. Al arrancar, el contenedor corre `alembic upgrade head` (crea el esquema en Supabase)
   y luego levanta uvicorn. El health check es `/health`.

## 3. Verificación en vivo

```
curl https://<tu-servicio>.onrender.com/health
curl https://<tu-servicio>.onrender.com/modules
curl -X POST https://<tu-servicio>.onrender.com/modules/herald/capabilities/propose_topic_questions \
  -H 'Content-Type: application/json' -d '{"name":"IA en medicina"}'
```

## 4. Frontend (Vercel) — pendiente

Cuando exista `apps/web`: New Project en Vercel → *Root Directory* = `apps/web`. Solo construye la
web; el monorepo no afecta el build. La web consume la API de Render.

## Correr local con keys

En `apps/backend/.env` pega las keys (ver `.env.example`) y:
```
cd apps/backend && uv run uvicorn jarvis.interfaces.api:app --port 8000
```
Sin `JARVIS_DATABASE_URL` usa almacenes en memoria; sin keys de audio, usa adaptadores interinos.
