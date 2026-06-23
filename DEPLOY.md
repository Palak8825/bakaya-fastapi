# Deploying Bakaya

Stack: **Replit** (FastAPI backend) + **Vercel** (React frontend) + **UptimeRobot** (keep-alive ping)

---

## STEP 1 — Push this repo to GitHub

This repo contains both the backend (`app/`) and the frontend (`frontend/`) — push it as one.

1. Go to https://github.com/new — create a **public** repo (e.g. `bakaya-fastapi`)
2. Open a terminal in `d:\bakaya-Final\bakaya-fastapi` and run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bakaya-fastapi.git
git push -u origin main
```

`.env` and `node_modules/` will not be committed — they are in `.gitignore`.

---

## STEP 2 — Deploy the backend on Replit

1. Go to https://replit.com → **Create Repl** → **Import from GitHub**
2. Paste your repo URL — Replit detects Python from `requirements.txt`

**Add secrets in Replit** (Secrets tab — not in a file):

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon / Postgres connection string |
| `GROQ_API_KEY` | Your Groq API key |
| `EMAIL_MODE` | `real` |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Your Gmail app password |
| `DEMO_RECIPIENT_EMAIL` | Demo fallback inbox (optional) |
| `ALLOWED_ORIGINS` | `*` ← update to your Vercel URL after Step 3 |

3. In the Replit Shell, run once to set up the database:
```bash
python setup_db.py && python seed.py
```

4. Click **Deploy** → **Autoscale** → Deploy.

Your backend URL will be: `https://bakaya-fastapi--YOUR_USERNAME.replit.app`

Test it: `https://YOUR_REPLIT_URL/api/health` should return `{"status":"ok"}`

---

## STEP 3 — Deploy the frontend on Vercel

1. Go to https://vercel.com → **Add New Project** → **Import Git Repository**
2. Import the same GitHub repo from Step 1
3. In **Configure Project**:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. **No environment variables needed** — `frontend/vercel.json` handles the API routing

Before deploying, confirm `frontend/vercel.json` has your actual Replit URL:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://bakaya-fastapi--YOUR_USERNAME.replit.app/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Deploy — Vercel gives you a URL like `https://bakaya.vercel.app`.

**How this works**: the browser calls `/api/invoices` on the Vercel domain → Vercel rewrites it to your Replit backend. From the browser's perspective it's same-origin, so there's no CORS issue. No frontend code changes needed.

---

## STEP 4 — Lock CORS to your Vercel domain (optional but good practice)

In Replit Secrets, update `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS=https://bakaya.vercel.app
```

Restart the deployment. Now only your Vercel frontend can call the backend directly.

---

## STEP 5 — Set up UptimeRobot (keep the backend warm)

Replit autoscale deployments sleep after inactivity. UptimeRobot pings `/api/health`
every 5 minutes to prevent that.

1. Go to https://uptimerobot.com → **Sign Up Free**
2. **Add New Monitor**:
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Bakaya FastAPI`
   - URL: `https://YOUR_REPLIT_URL/api/health`
   - Monitoring Interval: **5 minutes**
3. Click **Create Monitor**

---

## STEP 6 — The cold test (do not skip)

After everything is deployed:

1. Leave both services alone for **1 hour**
2. Open the Vercel URL on your **phone using mobile data** (not home WiFi — genuinely cold)
3. The page should load and show invoice data within a few seconds

If it spins → the backend slept. Check UptimeRobot is active and the health URL responds.

---

## Architecture summary

```
Browser
  │ GET /api/invoices (same-origin Vercel call)
  ▼
Vercel (React static site — always-on, free)
  │ vercel.json rewrites → https://bakaya-fastapi--username.replit.app/api/invoices
  ▼
Replit (FastAPI — autoscale, kept warm by UptimeRobot)
  │ SQLAlchemy query
  ▼
Neon Postgres
```

The browser never makes a cross-origin request — Vercel's edge does the forwarding.
