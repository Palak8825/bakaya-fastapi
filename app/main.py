"""
main.py = your Express app.ts + the server bootstrap.

  Express                              FastAPI
  -------                              -------
  const app = express()           ->   app = FastAPI()
  app.use(cors())                 ->   app.add_middleware(CORSMiddleware, ...)
  app.use(express.json())         ->   (built in)
  app.use("/api", routes)         ->   app.include_router(...)
  app.listen(PORT)                ->   `uvicorn app.main:app` (CLI)

Visit /docs for interactive auto-generated API docs (the OpenAPI spec FastAPI
builds from your Pydantic models — replaces hand-maintained openapi.yaml).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routes import buyers, invoices, dashboard, escalation, odr

app = FastAPI(title="Bakaya API (FastAPI edition)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One line per router — same as app.use(...) in Express.
app.include_router(buyers.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(escalation.router)
app.include_router(odr.router)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
