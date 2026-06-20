# Bakaya — FastAPI edition (complete learning port)

A full parallel backend for Bakaya, rebuilt in Python/FastAPI to mirror the
TypeScript/Express version. Same JSON contract (camelCase) → the existing React
frontend works against it unchanged. **Every route is built and runs.**

## Run
```bash
pip install -r requirements.txt
python seed.py                                  # SQLite db + 3 sample invoices
uvicorn app.main:app --reload --port 8099
```
Open **http://localhost:8099/docs** for interactive auto-generated API docs.

## Endpoints (all working)
| Route | What it does |
|---|---|
| `GET  /api/buyers` `POST /api/buyers` `PATCH /api/buyers/{id}` | buyer CRUD |
| `GET  /api/invoices` `POST /api/invoices` | invoice list/create (+ live interest) |
| `POST /api/invoices/{id}/draft` | LLM draft (Groq) — no send |
| `POST /api/invoices/{id}/send`  | draft + email + log + advance stage |
| `POST /api/escalation/run`      | **autonomous sweep** over the whole book |
| `GET  /api/invoices/{id}/odr-pack` | downloadable **PDF** filing pack |
| `GET  /api/dashboard/summary`   | live aggregate metrics |

## Quick test
```bash
curl localhost:8099/api/dashboard/summary
curl -X POST localhost:8099/api/escalation/run
curl localhost:8099/api/invoices/1/odr-pack -o odr.pdf
```

## Map to the TS app (what to study, in order)
| File | TS equivalent | Teaches |
|---|---|---|
| `app/rules.py` | `interest.ts` | pure logic — ports 1:1 |
| `app/models.py` | Drizzle schema | SQLAlchemy models |
| `app/schemas.py` | Zod schemas | Pydantic + **camelCase aliasing** (the gotcha) |
| `app/database.py` | Drizzle `db` client | per-request session via Depends() |
| `app/drafting.py` | `drafting.ts` | Groq call + template fallback |
| `app/notify.py` | `notify.ts` / `emailer.py` | smtplib email |
| `app/routes/invoices.py` | `invoices.ts` | path params, validated body, /send orchestration |
| `app/routes/escalation.py` | `escalation.ts` | the autonomous sweep (idempotent stage guard) |
| `app/routes/odr.py` | `odr.ts` | PDF generation (fpdf2 instead of pdfkit) |
| `app/routes/dashboard.py` | `dashboard.ts` | aggregate metrics from the DB |
| `app/main.py` | `app.ts` | app + router wiring; free `/docs` |

## Config (env vars / .env)
`DATABASE_URL` (defaults to local SQLite — **use a separate Postgres from the TS app**),
`GROQ_API_KEY` (set to get real LLM drafts; without it, drafts fall back to templates),
`EMAIL_MODE` (`real`/`simulation`), `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `DEMO_RECIPIENT_EMAIL`.

## Notes / honest gaps
- The escalation sweep sends every stage autonomously (`approved_by_owner=False`).
  Production would gate `formal_demand`/`odr_ready` behind owner approval.
- SQLite is the default for zero-setup learning; switch `DATABASE_URL` to Postgres for real use.
- Migrations: `init_db()` create-tables is dev-only; use Alembic for real Postgres.
