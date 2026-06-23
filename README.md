# Bakaya AI — MSME Accounts-Receivable Desk

> **Team:** The Edge Cases · BITS Pilani, Hyderabad Campus · CS 2nd Year  
> **Competition:** InnovateZ 2026  
> **Stack:** React · FastAPI · PostgreSQL · Groq (llama-3.3-70b) · fpdf2

---

## The Problem

Large firms run dedicated accounts-receivable desks to chase payments and protect cash flow.  
MSMEs cannot afford one — so the owner does it personally, and then stops doing it to protect the relationship.

| Stat | Figure | Source |
| ---- | ------ | ------ |
| MSME receivables locked in delayed payments (India) | **₹7.34 lakh crore** (Mar 2024) | GAME–FISME–C2FO, *Delayed Payments Report 3.0* (2025) |
| Share owed to **micro & small** suppliers | ~80% | GAME–D&B–Omidyar, *Delayed Payments Report* |
| Formally disputed dues on MSME Samadhaan Portal | ₹22,363 Cr (Jul 2025) | Min. of MSME, Lok Sabha reply |
| Avg. days to get paid — micro enterprise | **176 days** | CMIE Prowess analysis, 2019 |
| Statutory payment limit | **45 days** | MSMED Act 2006, s.15 |
| Udyam-registered MSMEs (eligible for MSMED protection) | **7.83 crore** (Feb 2026) | Ministry of MSME (PIB) |

**The real blocker is fear, not process.** Owners avoid chasing payments to protect the relationship, so working capital stays stuck for months. Bakaya steps in as an external AR desk — the system asks, never the owner.

**Bakaya** earns a **2–5% facilitation fee** on amounts it helps recover. The unit economics are simple: every ₹1,000 crore of receivables recovered through Bakaya generates ₹20–50 crore in revenue. Against a ₹7.34 lakh crore market — ~80% of it owed to the micro and small suppliers Bakaya serves — even a low-single-digit share of recovered receivables is a multi-hundred-crore opportunity. The near-term wedge is the **0–90 day pre-litigation window**, where no incumbent operates.

---

## The Solution

**Bakaya AI** is an agentic system that monitors invoices against the MSMED statutory timeline. It:

- Sends reminders in the supplier's trade language at the right tone for each escalation stage
- Tracks legal interest accruals in real time (deterministically — no LLM involved in the maths)
- Auto-compiles evidence packs for the MSME ODR Portal
- Depersonalises the collection follow-up so the owner never has to ask awkwardly

> *The buyer's cost of stalling just changed.*

### The Escalation Ladder — Worked Example

**Context:** Selvam runs a Tirupur garment unit. A buyer owes ₹1.8L past the 45-day mark.

```
DAY 0    ── Eligibility Check
              Bakaya matches invoice dates against Selvam's Udyam registration
              to confirm the MSMED clock applies (Silpi Industries SC 2021 rule).

DAY 30   ── Relationship-Safe Nudge
              A polite reminder goes out in Tamil, sent under the business name —
              not Selvam's own. No mention of interest or legal action yet.

DAY 46   ── The Tax Nudge
              Statutory interest starts accruing. Bakaya flags the Section 43B(h)
              tax cost to the buyer: this outstanding amount is NOT deductible
              until paid. The buyer now has a financial incentive to settle.

DAY 75   ── Formal Demand
              Bakaya drafts a formal demand notice with exact principal +
              compound interest at 3× RBI Bank Rate. Tone is firm, professional.

DAY 90+  ── ODR Preparation
              Full filing pack assembled: purchase orders, delivery logs,
              interest workings → ready to submit to odr.msme.gov.in.
```

**Why the escalation is credible:** Filing at the MSME Facilitation Council is free for the supplier · the council must rule within 90 days · buyers must deposit **75% of any award** to appeal, so they cannot simply stall.

---

## Why Not Just Use ChatGPT / Claude / Gemini?

| Capability | Bakaya | Generic LLM |
|---|---|---|
| Statutory interest maths | Deterministic compound calculation at 3× RBI Bank Rate, monthly rests, from day 46 — auditable, reproducible | Unreliable; LLMs hallucinate financial figures |
| Stage-aware escalation | 5-stage state machine with date-driven thresholds; stage-index guard prevents re-sending the same notice | No state; no idempotency |
| Udyam eligibility check | Validates Udyam registration predates the invoice (per Silpi Industries SC 2021) | No domain guardrail |
| Autonomous book sweep | One API call walks every overdue invoice, drafts, sends, logs, and advances stage | Manual, one invoice at a time |
| ODR filing pack | Pre-filled, legally structured PDF with interest workings and escalation history — uploadable to odr.msme.gov.in | Cannot produce a legally correct, case-specific PDF |
| Section 43B(h) flag | Computed per invoice; included in notices automatically when applicable | No integration with Indian tax law triggers |
| LLM's actual role | Tone and language only — numbers are passed in, never computed by the model | Trusted to compute numbers (hallucination risk) |

---

## Competitive Positioning

| Alternative | Gap |
|---|---|
| Vyapar / Khatabook / Zoho | Generic payment reminders — legally blind; no 45-day clock, no interest tracking, no legal leverage |
| CA & legal recovery firms | Upfront fees; engage only after the relationship is already damaged |
| Govt MSME ODR Portal | Starts only when a dispute is filed — nothing addresses the 90-day window before litigation |
| Owner's WhatsApp messages | Solves nothing; the fear of damaging the relationship is the blocker |

**Bakaya's edge:** Pre-dispute automation capturing the overlooked 0–90 day window · depersonalised chasing (the AR desk effect) · per-invoice legal layer no app has · vernacular-first notices in the language the trade actually runs in.

---

## Live Demo

**[https://innovate-edge-the-edge-cases-bakaya.vercel.app](https://innovate-edge-the-edge-cases-bakaya.vercel.app)**

The live app is pre-loaded with three sample invoices across three buyers, all dated more than 90 days ago so every escalation stage is active.

### What to try

| What to do | Where to find it |
|---|---|
| See aggregate overdue amounts, interest accrued, and stage breakdown | **Dashboard** (home page) |
| Browse buyers and their Udyam registration details | **Buyers** tab |
| View all invoices with live interest ticking in real time | **Invoices** tab |
| Click an invoice → see full escalation history, interest workings, and Udyam eligibility status | **Invoice detail** page |
| Draft a notice for a specific invoice (Groq LLM or template fallback) | Invoice detail → **Draft Notice** |
| Send a notice email and advance the escalation stage | Invoice detail → **Send Notice** |
| Run the autonomous sweep — escalates every eligible invoice in one click | **Escalation** tab → **Run Sweep** |
| Download a ready-to-file ODR PDF for an `odr_ready` invoice | Invoice detail → **Download ODR Pack** |
| Add a new buyer or invoice | **Buyers / Invoices** tab → **Add** button |

### What the demo shows end-to-end

1. Open the **Dashboard** — you'll see total overdue, interest accrued, and how many invoices are at each stage.
2. Go to **Invoices** → click any invoice → the detail page shows compound interest calculated to the day, the Udyam eligibility check, and the full escalation timeline.
3. Hit **Draft Notice** — Groq drafts a stage-appropriate message in the buyer's language. If the API key isn't set, a deterministic template fires instead.
4. Hit **Send Notice** — the email goes to the buyer's address (or the demo inbox if the buyer email is invalid or missing).
5. Go to **Escalation → Run Sweep** — one click walks the entire overdue book, drafts and sends notices for every eligible invoice, and advances all stages.
6. On any `odr_ready` invoice, click **Download ODR Pack** — you get a PDF with interest workings, escalation history, and a pre-filled MSME Facilitation Council claim statement.

---

## How It Works — Under the Hood

### Data flow for an autonomous escalation sweep

```
POST /api/escalation/run
  │
  ├─ DB: load all (Invoice JOIN Buyer)
  │
  ├─ rules.py ── get_escalation_stage(invoice_date)
  │     5-stage ladder: none → nudge → tax_nudge → formal_demand → odr_ready
  │     Thresholds: 30 / 46 / 75 / 90 days since invoice date
  │     Pure date arithmetic — no network, no LLM
  │
  ├─ rules.py ── calculate_interest(amount, invoice_date)
  │     Rate    = 3 × RBI Bank Rate = 16.5% p.a. (June 2026)
  │     Method  = compound, monthly rests, starting day 46
  │     Returns = { principal, totalInterest, totalDue, msmedDaysOverdue,
  │                 applicableRate, section43bhApplies }
  │     All Decimal — no float rounding errors in legal amounts
  │
  ├─ Stage-index guard (idempotency)
  │     Only acts if computed_stage_index > stored_stage_index
  │     Re-running the sweep never re-sends the same notice
  │
  ├─ drafting.py ── draft_message(stage, buyer_name, numbers…, language)
  │     Primary:  Groq API → llama-3.3-70b-versatile
  │               Prompt injects pre-computed numbers; LLM writes tone only
  │               Tone per stage: warm nudge → tax alert → formal → final
  │     Fallback: deterministic template (always produces a draft; no API key needed)
  │
  ├─ Email recipient resolution (see Email Routing section below)
  │
  ├─ notify.py ── send_notice(to, subject, body)
  │     EMAIL_MODE=real       → Gmail SMTP (smtplib)
  │     EMAIL_MODE=simulation → console log (safe for demos)
  │     Guard: if "@" not in address → status: failed (no send attempted)
  │
  └─ DB: write EscalationEvent row, advance invoice.escalation_stage, commit
```

### Email Routing — Full Logic

Email recipient resolution differs between the manual dashboard send and the automatic sweep.

#### Manual send (dashboard "Send Notice" button — `POST /api/invoices/{id}/send`)

```
Priority chain (first valid address wins):
  1. body.to          — explicit override in the request body
  2. buyer.email      — the buyer's stored email (only if it contains "@")
  3. DEMO_RECIPIENT_EMAIL — env-level demo inbox fallback

If none resolve → HTTP 422 "No recipient"
```

**Invalid email fallback:** If the buyer's email is missing or malformed (no `@`), it is skipped and the request falls through to `DEMO_RECIPIENT_EMAIL`. This means adding a placeholder like `pending` or a blank email for a buyer does not break the send — it just routes to the demo inbox until a real address is set.

#### Autonomous sweep (`POST /api/escalation/run`)

```
Priority chain:
  1. DEMO_RECIPIENT_EMAIL — always wins if set (demo/testing mode)
  2. buyer.email          — only used if valid (contains "@")

If neither resolves → delivery_status: "no_email" (sweep continues to next invoice)
```

The sweep intentionally puts the demo address first so that a single env var can redirect all automated emails to a test inbox without touching any buyer records.

#### Final guard in `notify.py`

Regardless of which path resolves the recipient, `send_notice()` performs a last-resort check: if the address contains no `@`, it returns `{"status": "failed", "detail": "Invalid recipient email"}` without attempting an SMTP connection.

#### Email mode behaviour

| `EMAIL_MODE` | Gmail creds present | Behaviour |
|---|---|---|
| `simulation` (default) | any | Logs to console; returns `status: simulated` |
| `real` | yes | Sends via Gmail SMTP; returns `status: sent` |
| `real` | no | Falls back to simulation; returns `status: simulated` |
| any | any | Address missing `@` → `status: failed` (no send) |

---

### ODR PDF generation

`GET /api/invoices/{id}/odr-pack` builds a downloadable PDF (fpdf2) containing:

- Parties (supplier / buyer contact details)
- Invoice summary (number, date, principal)
- Full MSMED s.16 interest workings (rate, months, total)
- Escalation timeline (every event with date, stage, channel)
- Ready-to-file claim statement citing MSMED Act ss.15–17
- Document checklist (invoice copy, Udyam cert, PO, delivery proof, etc.)
- Recovery priority flag (HIGH / MEDIUM / LOW) based on days overdue

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               React Frontend  (TypeScript + Vite)            │
│     Buyers · Invoices · Dashboard · Escalation views         │
│     Connects via Vite proxy (/api → localhost:8099)          │
└────────────────────────┬─────────────────────────────────────┘
                         │  JSON (camelCase, same contract as TS backend)
┌────────────────────────▼─────────────────────────────────────┐
│                  FastAPI  (Python 3.12+)                     │
│                                                              │
│  /buyers   /invoices   /dashboard   /escalation   /odr-pack  │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │  rules.py   │  │ drafting.py  │  │     notify.py       │  │
│  │ MSMED law   │  │ Groq / tmpl  │  │  SMTP / simulate    │  │
│  │ pure math   │  │ tone only    │  │  + recipient guard  │  │
│  └─────────────┘  └──────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           SQLAlchemy ORM                             │    │
│  │   Buyer · Invoice · EscalationEvent                  │    │
│  └──────────────────────┬───────────────────────────────┘    │
└─────────────────────────┼────────────────────────────────────┘
                          │
              ┌───────────┴────────────┐
              │  PostgreSQL / Neon     │
              │   (SQLite for local)   │
              └────────────────────────┘

External services
  Groq API  →  llama-3.3-70b-versatile  (LLM drafting; optional)
  Gmail SMTP                             (real email mode; optional)
  odr.msme.gov.in                        (manual upload destination for ODR pack)
```

**Planned (not yet wired):**

```
  Bhashini API           →  vernacular translation (Tamil, Hindi, Marathi…)
  WhatsApp Business API  →  outbound delivery channel
  Tally / Zoho / Vyapar  →  invoice import integrations
```

---

## File Map

```
app/
├── main.py          FastAPI app + router wiring + CORS
├── config.py        Pydantic settings (reads .env)
├── database.py      SQLAlchemy engine + per-request session (Depends)
├── models.py        Buyer · Invoice · EscalationEvent ORM models
├── schemas.py       Pydantic response schemas (camelCase aliasing)
├── rules.py         MSMED rules engine — pure functions, no I/O
│                    get_escalation_stage() · calculate_interest() · is_eligible()
├── drafting.py      Groq LLM drafting + deterministic template fallback
├── notify.py        Email delivery — SMTP real / simulation + @ validity guard
└── routes/
    ├── buyers.py    Buyer CRUD
    ├── invoices.py  Invoice list/create/draft/send (with invalid-email fallback)
    ├── escalation.py POST /escalation/run — autonomous sweep
    ├── odr.py       GET /invoices/{id}/odr-pack — PDF generation
    └── dashboard.py GET /dashboard/summary — aggregate metrics

seed.py              Populate DB with 3 buyers + 3 sample invoices
setup_db.py          Schema-only init (no seed data)

frontend/
├── src/             React app (TypeScript + Vite)
│   ├── pages/       Dashboard · Buyers · Invoices · AddBuyer · AddInvoice · InvoiceDetail
│   ├── components/  UI primitives (shadcn/ui) + Sidebar layout
│   ├── hooks/       use-mobile · use-toast
│   └── lib/
│       ├── utils.ts
│       └── api-client/   Generated API client + React Query hooks
├── public/          Static assets (favicon, images)
├── vite.config.ts   Dev proxy (/api → localhost:8099)
└── vercel.json      Production rewrites (/api → Replit backend)

tests/
└── test_core.py     Unit tests for rules.py, notify.py, drafting.py (40 tests)
```

---

## Frontend — Current State

The React frontend is a **TypeScript + Vite** app. It was originally built against an Express/Node backend and connects to this FastAPI backend without any component changes — the API contract (routes + camelCase JSON keys) is identical.

### What the frontend currently has

| View | What it shows |
|---|---|
| **Dashboard** | Aggregate stats — total overdue amount, total interest accrued, invoice counts by stage, stage-breakdown bar |
| **Buyers** | List of buyers; add/edit buyer (name, email, language, Udyam registration date) |
| **Invoices** | List of invoices with live interest; add invoice; per-invoice detail with escalation history |
| **Send Notice** | Per-invoice manual send — drafts via Groq or template, shows preview, sends email, advances stage |
| **Escalation Sweep** | One-click "Run Sweep" that calls `POST /api/escalation/run` and shows per-invoice results |
| **ODR Pack** | Download button on any `odr_ready` invoice — fetches the PDF from `/api/invoices/{id}/odr-pack` |

### How it connects to this backend

#### Local development

`vite.config.ts` already has the proxy configured:

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

The frontend calls `/api/...`, Vite forwards it to FastAPI automatically.

#### Production deployment (current live setup)

```
Browser
  └─ Vercel  (serves React static files)
       └─ /api/* rewrites → https://bakaya-fastapi--Palak8825.replit.app
                                  (FastAPI backend on Replit)
```

The rewrite is configured in `frontend/vercel.json`. No `VITE_API_URL` env var needed — the frontend always calls `/api/...` and Vercel handles the forwarding.


### Known frontend gaps

- Owner-approval gate for `formal_demand` / `odr_ready` stages is not in the UI — the sweep is fully autonomous (demo-appropriate; production should gate high-stakes stages)
- Language selection on buyers is stored but Bhashini translation is not yet wired

---

## API Reference

| Method | Route | What it does |
|---|---|---|
| `GET` | `/api/buyers` | List all buyers |
| `POST` | `/api/buyers` | Create a buyer |
| `PATCH` | `/api/buyers/{id}` | Update a buyer |
| `GET` | `/api/invoices` | List invoices with live interest calculated |
| `POST` | `/api/invoices` | Create an invoice |
| `POST` | `/api/invoices/{id}/draft` | Draft a notice (Groq / template) — does not send |
| `POST` | `/api/invoices/{id}/send` | Draft + email + log + advance stage |
| `POST` | `/api/escalation/run` | **Autonomous sweep** — walks entire book, escalates all eligible invoices |
| `GET` | `/api/invoices/{id}/odr-pack` | Download ODR filing pack PDF |
| `GET` | `/api/dashboard/summary` | Live aggregate metrics (total overdue, interest accrued, stage breakdown) |

Interactive docs at **http://localhost:8099/docs** (auto-generated OpenAPI from Pydantic models).

---

## Data Sources

| Source | Role in the system |
|---|---|
| **MSMED Act 2006, ss.15–17** | 45-day payment limit; compound interest entitlement; ODR filing right |
| **RBI Bank Rate 5.5% (June 2026)** | `STATUTORY_RATE = 3 × Bank Rate = 16.5% p.a.` — hardcoded in `rules.py` as `RBI_BANK_RATE` |
| **Income Tax Act, s.43B(h)** | Buyer's deductibility flag — buyer cannot deduct this expense until it is paid |
| **Silpi Industries v. Kerala SRTC (SC 2021)** | Eligibility guardrail — MSMED protection applies only if Udyam registration predates the invoice |
| **MSME ODR Portal (odr.msme.gov.in)** | Filing destination referenced in the ODR pack PDF and claim statement |
| **Groq API (llama-3.3-70b-versatile)** | LLM for drafting notice text — tone and language only; never computes figures |
| **PostgreSQL / SQLite** | Buyer, invoice, and escalation-event storage |
| **`seed.py` mock data** | 3 sample invoices across 3 buyers for zero-setup demo |

---

## Demo Scenarios

### Scenario A — Autonomous sweep

**Input:** Three seed invoices all dated > 90 days ago (`python seed.py`).

```bash
curl -X POST localhost:8099/api/escalation/run
```

**What happens:**
1. `rules.py` computes `odr_ready` for all three invoices (age > 90 days).
2. Stage-index guard: stored stage is `none`, computed is `odr_ready` → act.
3. `drafting.py` calls Groq; produces a final-notice draft in the buyer's language.
4. `notify.py` logs to console (simulation) or sends via Gmail SMTP (real).
5. Three `EscalationEvent` rows written; all invoices advance to `odr_ready`.

**Response:**
```json
{
  "processed": 3,
  "escalated": 3,
  "results": [
    {
      "invoiceId": 1,
      "invoiceNumber": "INV-001",
      "action": "escalated",
      "fromStage": "none",
      "toStage": "odr_ready",
      "deliveryStatus": "simulated",
      "source": "llm"
    }
  ]
}
```

**Why it's useful:** One API call handles the entire overdue book. Re-running the sweep is safe — no duplicate notices.

---

### Scenario B — ODR filing pack PDF

```bash
curl localhost:8099/api/invoices/1/odr-pack -o ODR-Pack-INV-001.pdf
```

**Output:** A ready-to-upload PDF containing:

- Parties and invoice details
- Interest workings: `Rs X principal × (1 + 16.5%/12)^months = Rs Y total`
- Escalation history with dates and channels
- Claim statement citing MSMED Act ss.15–17
- Document checklist (invoice, Udyam cert, PO, delivery proof, bank statement)

---

### Scenario C — Invalid buyer email falls back to demo inbox

If a buyer is added from the dashboard with a placeholder or missing email:

```bash
# buyer has email = "pending" or ""
curl -X POST localhost:8099/api/invoices/2/send \
  -H "Content-Type: application/json" \
  -d '{"stage": "nudge", "language": "English"}'
```

**What happens:** `"pending"` contains no `@`, so it is skipped. If `DEMO_RECIPIENT_EMAIL` is set in `.env`, the notice goes there. If not, the API returns HTTP 422.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in variables below
python seed.py                # creates bakaya.db + 3 sample invoices
uvicorn app.main:app --reload --port 8099
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./bakaya.db` | PostgreSQL connection string for prod (`postgresql+psycopg://…`) |
| `GROQ_API_KEY` | _(empty)_ | LLM drafting — omit to use template fallback (app still works) |
| `EMAIL_MODE` | `simulation` | `real` to send actual emails via Gmail SMTP |
| `GMAIL_ADDRESS` | _(empty)_ | Sender address for real email |
| `GMAIL_APP_PASSWORD` | _(empty)_ | Gmail app password (not your login password) |
| `DEMO_RECIPIENT_EMAIL` | _(empty)_ | Redirect all outbound notices to one inbox; also the fallback when buyer email is invalid |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins — lock to your Vercel URL in production |

> Full deployment walkthrough: [DEPLOY.md](DEPLOY.md) · Frontend connection details: [CONNECTING.md](CONNECTING.md)

### Quick smoke test

```bash
curl localhost:8099/api/dashboard/summary
curl -X POST localhost:8099/api/escalation/run
curl localhost:8099/api/invoices/1/odr-pack -o odr.pdf
```

---

## Key Dependencies

| Package | Version | Role |
|---|---|---|
| `fastapi` | latest | Web framework |
| `uvicorn[standard]` | latest | ASGI server |
| `sqlalchemy` | latest | ORM (Postgres + SQLite) |
| `pydantic` + `pydantic-settings` | latest | Schema validation, env config, camelCase aliasing |
| `groq` | latest | LLM API client |
| `fpdf2` | latest | PDF generation for ODR pack |
| `psycopg[binary]` | latest | PostgreSQL driver |

---

## Current Status & Honest Gaps

| Feature | Status |
|---|---|
| Buyer CRUD | Working |
| Invoice create / list with live interest | Working |
| Escalation sweep (autonomous) | Working |
| LLM drafting via Groq | Working (template fallback if no API key) |
| Email — simulation mode | Working |
| Email — real Gmail SMTP | Working |
| Invalid buyer email → demo inbox fallback | Working |
| ODR filing pack PDF | Working |
| Dashboard aggregate metrics | Working |
| Udyam eligibility date check | Working — surfaced in invoice detail view with Silpi Industries (SC 2021) warning |
| Owner-approval gate for `formal_demand` / `odr_ready` | Gap — sweep is fully autonomous (demo only; production must gate these stages) |
| Alembic migrations | Not yet — `init_db()` is dev-only; production needs Alembic |
| Bhashini vernacular translation | Planned; `language` field on Buyer model exists; not yet wired |
| WhatsApp Business API delivery | Planned; email is the current delivery channel |
| Tally / Zoho / Vyapar invoice import | Planned; manual entry only in MVP |

---

## Legal References

- **MSMED Act 2006, Section 15** — buyer must pay within 45 days of acceptance
- **MSMED Act 2006, Section 16** — compound interest at 3× RBI Bank Rate accrues from day 46
- **MSMED Act 2006, Sections 17–23** — Facilitation Council / ODR filing rights
- **Income Tax Act, Section 43B(h)** — buyer's deduction on MSME payments is cash-basis only (introduced Finance Act 2023)
- **Silpi Industries v. Kerala SRTC, SC 2021** — Udyam registration must predate the invoice for MSMED protection to apply
