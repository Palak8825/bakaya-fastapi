"""
Drafting layer = your drafting.ts (TS) and Streamlit drafting.py.

The LLM writes the message AROUND numbers the rules engine already computed —
it never computes a number itself. If Groq is unavailable (no key, rate limit,
network), we fall back to a deterministic template, so a draft is ALWAYS produced.

Returns (message, source) where source ∈ {"llm", "fallback"}.
"""
from .config import settings

# Tone per stage — mirrors TONE_BY_STAGE in the TS app.
TONE_BY_STAGE = {
    "nudge": "warm, friendly, pre-deadline heads-up; do NOT mention interest or tax",
    "tax_nudge": "warm but matter-of-fact; note interest has started and the buyer's 43B(h) tax risk",
    "formal_demand": "formal and firm but professional; clear demand with amount and interest",
    "odr_ready": "formal final notice; matter is ready for the MSME ODR Portal",
}


def _template(stage, buyer_name, invoice_number, amount, interest, total_due, days_overdue, flag43bh):
    """Deterministic fallback — always works, no API needed."""
    interest_line = (
        f" Interest of Rs {interest:,.0f} has accrued (total due Rs {total_due:,.0f})."
        if interest > 0 else ""
    )
    tax_line = (
        " Under Section 43B(h), this expense is deductible only in the year of actual payment."
        if flag43bh else ""
    )
    return (
        f"Dear {buyer_name}, regarding invoice {invoice_number} for Rs {amount:,.0f}, "
        f"now {days_overdue} days past the 45-day limit.{interest_line}{tax_line} "
        f"Please arrange payment promptly. — Accounts Desk (via Bakaya)"
    )


def draft_message(stage, buyer_name, invoice_number, amount, interest,
                  total_due, days_overdue, rate_pct, flag43bh, language="English"):
    fallback = _template(stage, buyer_name, invoice_number, amount, interest,
                         total_due, days_overdue, flag43bh)

    if not settings.groq_api_key:
        return fallback, "fallback"

    try:
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)

        tone = TONE_BY_STAGE.get(stage, "polite and professional")
        interest_fact = (
            f"Interest accrued: Rs {interest:,.0f} at {rate_pct}% p.a. (3x RBI Bank Rate). "
            f"Total payable: Rs {total_due:,.0f}."
            if interest > 0 else "No statutory interest yet."
        )
        tax_fact = (
            "Mention that under Section 43B(h) the buyer can only deduct this expense once paid."
            if flag43bh else "Do NOT mention tax deductions."
        )
        prompt = (
            f"Write a payment-reminder message in {language}. Output ONLY the message text.\n"
            f"Tone: {tone}.\n"
            f"Buyer: {buyer_name}. Invoice {invoice_number}, principal Rs {amount:,.0f}, "
            f"{days_overdue} days overdue. {interest_fact}\n"
            f"{tax_fact}\n"
            f"Do not invent or change any number. Keep under 130 words. "
            f"Sign off as 'Accounts Desk (via Bakaya)'."
        )

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.4,
        )
        text = resp.choices[0].message.content.strip()
        return (text, "llm") if text else (fallback, "fallback")
    except Exception:
        return fallback, "fallback"
