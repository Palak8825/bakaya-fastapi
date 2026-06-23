# How the frontend and backend connect

The frontend (`frontend/`) and backend (`app/`) live in the same repo but are completely decoupled — they communicate only over HTTP. The frontend never imports backend code.

---

## Local development

`frontend/vite.config.ts` already has the proxy configured:

```ts
server: {
  proxy: {
    "/api": "http://localhost:8099",
  },
},
```

Run both servers:

```bash
# terminal 1 — FastAPI backend
uvicorn app.main:app --reload --port 8099

# terminal 2 — React frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. The frontend calls `/api/...`, Vite forwards those requests to FastAPI on port 8099, and it all works. You never touch any component to switch backends.

**Why it's seamless:** this FastAPI backend exposes the same routes (`/api/invoices`, `/api/buyers`, etc.) and returns the same camelCase JSON keys (`invoiceNumber`, `escalationStage`, ...) as the original Express backend. The `schemas.py` aliasing handles the camelCase conversion automatically.

---

## Production (Vercel + Replit)

In production there is no Vite server, so the proxy doesn't exist. `frontend/vercel.json` takes its place:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://bakaya-fastapi--Palak8825.replit.app/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Vercel serves the built React static files and rewrites any `/api/*` request to the Replit backend. The browser always talks to the same Vercel domain — no cross-origin requests, no CORS headers needed between browser and backend.

The second rewrite (`/(.*)` → `/index.html`) handles SPA client-side routing so direct URL navigation (e.g. `/invoices/3`) doesn't 404.

---

## Database

The backend uses its own PostgreSQL database (Neon), separate from any other project's database. SQLAlchemy manages the schema — `setup_db.py` creates the tables on first run.

To use a local SQLite database instead (zero setup, good for development):

```bash
# Leave DATABASE_URL unset — defaults to sqlite:///./bakaya.db
python setup_db.py
python seed.py
uvicorn app.main:app --reload --port 8099
```

For a real Postgres (Neon, Railway, Render):
```
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

Put that in `.env` and run `python setup_db.py` once to create the schema.
