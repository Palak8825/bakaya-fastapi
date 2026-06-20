"""
Notify layer = your notify.ts (TS) and emailer.py (Streamlit) — you've already
written this exact thing twice. EMAIL_MODE switches real vs simulation.
"""
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from .config import settings


def send_notice(to: str, subject: str, body: str, sender_name: str = "Accounts Desk") -> dict:
    """Returns {status, detail}. status ∈ {sent, simulated, failed}."""
    to = (to or "").strip()
    if "@" not in to:
        return {"status": "failed", "detail": "Invalid recipient email"}

    mode = settings.email_mode
    have_creds = bool(settings.gmail_address and settings.gmail_app_password)

    # Simulation: default, or real-without-creds (safe fallback, like your TS layer)
    if mode != "real" or not have_creds:
        reason = "EMAIL_MODE!=real" if mode != "real" else "GMAIL creds not set"
        return {"status": "simulated", "detail": f"Simulated send to {to} ({reason})"}

    try:
        msg = EmailMessage()
        msg["From"] = formataddr((f"{sender_name} (via Bakaya)", settings.gmail_address))
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(settings.gmail_address, settings.gmail_app_password)
            server.send_message(msg)
        return {"status": "sent", "detail": f"Email sent to {to}"}
    except smtplib.SMTPAuthenticationError:
        return {"status": "failed", "detail": "Gmail rejected login — check app password"}
    except Exception as e:  # noqa: BLE001
        return {"status": "failed", "detail": f"Send failed: {e}"}
