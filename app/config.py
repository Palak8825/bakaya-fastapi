"""
Config — the FastAPI equivalent of reading process.env in your Express app.

In TS you sprinkled `process.env.GROQ_API_KEY` around. The Python convention is
to declare ALL env vars once, as a typed Settings object, and import it. You get
validation (a missing required var fails loudly at startup, like your index.ts
PORT check) and autocomplete.
"""
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Accepts NEON_DATABASE_URL (Replit) or DATABASE_URL (local .env) — both work.
    database_url: str = Field(
        default="sqlite:///./bakaya.db",
        validation_alias=AliasChoices("neon_database_url", "database_url"),
    )
    groq_api_key: str | None = None

    # Email (mirrors your notify.ts / emailer.py)
    email_mode: str = "simulation"                 # "real" | "simulation"
    gmail_address: str | None = None
    gmail_app_password: str | None = None
    demo_recipient_email: str | None = None

    # CORS — comma-separated allowed origins, e.g. "https://bakaya.vercel.app"
    # Defaults to * for local dev; lock to your Vercel URL in production.
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# One shared instance, imported everywhere — like a singleton config module.
settings = Settings()
