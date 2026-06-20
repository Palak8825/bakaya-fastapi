# Connecting this backend to the React frontend + setting up a separate database

## Part 1 — How the frontend connects

Your React app never imports backend code. It talks over HTTP: it sends requests
to URLs like `POST /api/invoices/3/send` and reads JSON back. So "connecting" the
frontend to this Python backend = making the frontend's requests reach this
server instead of the Express one. Two things make that work:

### 1a. Same URLs + same JSON keys (already done)
This FastAPI app exposes the SAME routes (`/api/invoices`, `/api/buyers`, etc.)
and returns the SAME camelCase keys (`invoiceNumber`, `escalationStage`, ...) as
the TS app. That's why the frontend can't tell the difference — the contract is
identical. (That camelCase matching is the `schemas.py` aliasing trick.)

### 1b. Point the frontend at this server
The frontend decides where "/api/..." goes. In dev (Vite) the clean way is a
proxy. In `artifacts/bakaya/vite.config.ts`, add a server proxy so `/api` calls
forward to this Python server on port 8099:

```ts
// vite.config.ts
export default defineConfig({
  // ...existing config...
  server: {
    proxy: {
      "/api": "http://localhost:8099",   // <- FastAPI instead of the Express port
    },
  },
});
```

Now run BOTH:
```bash
# terminal 1 — this backend
uvicorn app.main:app --reload --port 8099

# terminal 2 — the existing React frontend (unchanged)
cd artifacts/bakaya && pnpm dev
```
The React app calls `/api/...`, Vite forwards it to FastAPI, and it just works.
CORS is already enabled in `app/main.py` so direct browser calls work too.

> You do NOT copy or edit any React component. The only change is the one proxy
> line telling the frontend which backend to talk to.

### 1c. (Production) same idea, different knob
When deployed, you set the frontend's API base URL (env var like `VITE_API_URL`)
or put both behind one domain. Same principle: route `/api` to this server.

---

## Part 2 — A separate database with the same schema

**Why separate:** your TS app's Postgres is managed by Drizzle. If this Python
app (SQLAlchemy) writes to the same database, the two schema managers will
eventually conflict and could corrupt the data behind your submitted app. Keep
them isolated.

### Option A — zero setup (default): SQLite
Do nothing. `DATABASE_URL` defaults to a local `bakaya.db` file. Great for
learning. Run `python setup_db.py` then `python seed.py`.

### Option B — a real, separate Postgres (e.g. Neon, free)
1. Create a NEW database — e.g. a new project at neon.tech (or a new Render/Railway
   Postgres). This is a different database from your TS app's.
2. Copy its connection string. Make it psycopg-style:
   ```
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```
   Put that in `.env`. (Install the driver: `pip install "psycopg[binary]"`.)
3. Create the schema in it:
   ```bash
   python setup_db.py        # creates buyers, invoices, escalation_events
   python seed.py            # optional sample data
   ```
That's it — same three tables, same columns as the TS app, in a brand-new DB
that can't touch the original.

### Keeping schemas in sync later
`setup_db.py` create-tables is fine for first setup. Once you start CHANGING the
schema on a live Postgres, use Alembic (Python's migration tool, the Drizzle-kit
equivalent): `pip install alembic`, then `alembic init`. Not needed for learning.
