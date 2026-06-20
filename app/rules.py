"""
Rules engine — pure functions, no framework, no DB. This is the part that's
genuinely interchangeable between TS and Python: numbers and dates in, numbers
and strings out. It's a near-line-for-line twin of your TS interest.ts and your
Streamlit rules_engine.py.

This is also your "value beyond a generic LLM": deterministic, auditable MSMED
math that an LLM cannot be trusted to compute.
"""
from datetime import date
from decimal import Decimal

# --- Canonical constants (keep in ONE place, like RBI_BANK_RATE in interest.ts) ---
PAYMENT_LIMIT_DAYS = 45
RBI_BANK_RATE = Decimal("0.055")          # 5.50% (June 2026) — the Bank Rate, not repo
STATUTORY_RATE = RBI_BANK_RATE * 3        # 3× Bank Rate = 16.5% p.a., per MSMED s.16

# Canonical 5-stage ladder (clock = days since invoice date), matching the TS app.
STAGE_NONE = "none"
STAGE_NUDGE = "nudge"
STAGE_TAX_NUDGE = "tax_nudge"
STAGE_FORMAL_DEMAND = "formal_demand"
STAGE_ODR_READY = "odr_ready"
STAGE_ORDER = [STAGE_NONE, STAGE_NUDGE, STAGE_TAX_NUDGE, STAGE_FORMAL_DEMAND, STAGE_ODR_READY]


def days_since_invoice(invoice_date: date, today: date | None = None) -> int:
    today = today or date.today()
    return (today - invoice_date).days


def get_escalation_stage(invoice_date: date, today: date | None = None) -> str:
    """5-stage state machine. Same thresholds as getEscalationStageForInvoiceDate()."""
    since = days_since_invoice(invoice_date, today)
    if since >= 90:
        return STAGE_ODR_READY
    if since >= 75:
        return STAGE_FORMAL_DEMAND
    if since >= 46:
        return STAGE_TAX_NUDGE
    if since >= 30:
        return STAGE_NUDGE
    return STAGE_NONE


def is_eligible(invoice_date: date, udyam_date: date | None) -> bool:
    """Silpi Industries (SC 2021): s.16 protection only if Udyam predates invoice."""
    if udyam_date is None:
        return False
    return udyam_date < invoice_date


def calculate_interest(amount: float, invoice_date: date, today: date | None = None) -> dict:
    """Compound interest, monthly rests, at 3× Bank Rate, starting day 46.

    Returns a dict mirroring the TS calculateInterest() result so the API
    response shape can stay identical.
    """
    amount = Decimal(str(amount))
    since = days_since_invoice(invoice_date, today)
    days_overdue = max(0, since - PAYMENT_LIMIT_DAYS)

    if days_overdue <= 0:
        total_interest = Decimal("0")
    else:
        # Compound monthly: months elapsed since the limit, monthly rests.
        months = Decimal(days_overdue) / Decimal("30")
        monthly_rate = STATUTORY_RATE / Decimal("12")
        total = amount * ((1 + monthly_rate) ** months)
        total_interest = (total - amount).quantize(Decimal("0.01"))

    section_43bh = days_overdue > 0  # live once overdue (eligibility checked separately)

    return {
        "principal": float(amount),
        "totalInterest": float(total_interest),
        "totalDue": float(amount + total_interest),
        "msmedDaysOverdue": days_overdue,
        "applicableRate": float(STATUTORY_RATE),
        "section43bhApplies": section_43bh,
    }
