# Deploying Bakaya FastAPI — card-free, always-warm

Stack: **Replit** (FastAPI backend) + **Vercel** (React frontend) + **UptimeRobot** (keep-warm ping)

---

## STEP 1 — Push the backend to GitHub

You need the `bakaya-fastapi` folder in its own GitHub repo so Replit can import it.

1. Go to https://github.com/new — create a **public** repo called `bakaya-fastapi`
2. Open a terminal in this folder (`d:\bakaya-Final\bakaya-fastapi`) and run:

```bash
git init
git add .
git commit -m "Initial FastAPI backend"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/bakaya-fastapi.git
git push -u origin main
```

`.env` will NOT be committed — it's in `.gitignore`. Good.

---

## STEP 2 — Deploy the backend on Replit

1. Go to https://replit.com → **Create Repl** → **Import from GitHub**
2. Paste your repo URL: `https://github.com/YOUR_GITHUB_USERNAME/bakaya-fastapi`
3. Replit detects Python automatically from `requirements.txt`

**Add secrets in Replit** (Secrets tab in the sidebar — NOT in a file):

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+psycopg://neondb_owner:...@...neon.tech/neondb?sslmode=require` |
| `GROQ_API_KEY` | `gsk_...` |
| `EMAIL_MODE` | `real` |
| `GMAIL_ADDRESS` | `palak.agarwal.8825@gmail.com` |
| `GMAIL_APP_PASSWORD` | `tqeebtjjrbejzyjf` |
| `DEMO_RECIPIENT_EMAIL` | `palak.agarwal.8825@gmail.com` |
| `ALLOWED_ORIGINS` | `*` ← update to your Vercel URL after Step 3 |

4. In the Replit Shell tab, run once to set up the database:
```bash
python setup_db.py && python seed.py
```

5. Click **Deploy** (top-right) → choose **Autoscale** → Deploy.
   - Replit gives you a URL like: `https://bakaya-fastapi.YOUR_USERNAME.replit.app`
   - Test it: open `https://YOUR_REPLIT_URL/api/health` in a browser — should show `{"status":"ok"}`

**Copy that URL — you need it for Step 3.**

---

## STEP 3 — Deploy the frontend on Vercel

The React frontend is in `D:\Innovate-Edge-The-Edge-Cases\artifacts\bakaya`.

1. Go to https://vercel.com → **Add New Project** → **Import Git Repository**
2. Connect your GitHub and import the `Innovate-Edge-The-Edge-Cases` repo
3. In **Configure Project**:
   - **Root Directory**: `artifacts/bakaya`
   - **Framework Preset**: Vite
   - **Build Command**: `pnpm build` (or leave auto-detect)
   - **Output Directory**: `dist/public`
4. **No environment variables needed** — the `vercel.json` proxy handles routing

**Before deploying**, edit `artifacts/bakaya/vercel.json` and replace the placeholder:
```json
"destination": "https://REPLACE_WITH_YOUR_REPLIT_URL/api/:path*"
```
→ with your actual Replit URL from Step 2, e.g.:
```json
"destination": "https://bakaya-fastapi.yourusername.replit.app/api/:path*"
```

Commit and push that change, then deploy on Vercel.

Vercel gives you a URL like: `https://bakaya.vercel.app`

**How this works**: the browser calls `/api/invoices` on the Vercel domain → Vercel rewrites it to your Replit backend → response comes back. From the browser's perspective it's same-origin, so there's no CORS issue at all. No frontend code changes needed.

---

## STEP 4 — Lock CORS to your Vercel domain (optional but good practice)

In Replit Secrets, update `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS=https://bakaya.vercel.app
```

Restart the Replit deployment. Now only your Vercel frontend can call the backend directly.

---

## STEP 5 — Set up UptimeRobot (keep the backend warm)

Replit free/autoscale deployments can sleep after inactivity. UptimeRobot pings `/api/health`
every 5 minutes to prevent that, at no cost and no card required.

1. Go to https://uptimerobot.com → **Sign Up Free** (no card)
2. **Add New Monitor**:
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Bakaya FastAPI`
   - URL: `https://YOUR_REPLIT_URL/api/health`
   - Monitoring Interval: **5 minutes**
3. Click **Create Monitor**

That's it. UptimeRobot hits `/api/health` every 5 min → backend stays warm → judges never see a cold-start spin.

---

## STEP 6 — The cold test (do not skip)

After everything is deployed:

1. Leave both services completely alone for **1 hour**
2. Open the Vercel URL on your **phone using mobile data** (not your home WiFi, so it's genuinely cold)
3. The page should load and show invoice data within a few seconds

If it loads fast → judge-ready. If it spins → the backend slept (UptimeRobot may not be running yet, or there's a delay). Check that UptimeRobot is active and the health URL responds.

---

## Architecture summary

```
Browser
  │ GET /api/invoices (same-origin Vercel call)
  ▼
Vercel (React static site, always-on, free)
  │ vercel.json rewrites → https://bakaya-fastapi.replit.app/api/invoices
  ▼
Replit (FastAPI, autoscale, kept warm by UptimeRobot)
  │ SQLAlchemy query
  ▼
Neon Postgres (already live)
```

The browser never makes a cross-origin request — Vercel's edge does the forwarding.
No CORS headers needed between browser and backend for normal operation.
