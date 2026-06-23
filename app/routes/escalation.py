"""
Escalation router = escalation.ts — the autonomous "agentic" sweep.

POST /api/escalation/run walks the whole invoice book and, for each invoice
whose computed stage is AHEAD of its stored stage, drafts a notice, sends it,
logs the event, and advances the stage. This is the loop that makes Bakaya an
"agent" rather than a calculator: it decides and acts across the book in one go.

Note the stage-index guard: we only act when the invoice has genuinely advanced,
so re-running the sweep is safe (idempotent) — it won't re-send the same stage.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice, EscalationEvent
from ..rules import calculate_interest, get_escalation_stage, is_eligible, STAGE_ORDER
from ..drafting import draft_message
from ..notify import send_notice
from ..config import settings
from ..schemas import CamelModel

router = APIRouter(prefix="/api", tags=["escalation"])

STAGE_SUBJECT = {
    "nudge": "Payment Reminder",
    "tax_nudge": "Overdue Notice — Tax Alert",
    "formal_demand": "Formal Demand Notice",
    "odr_ready": "Final Notice — ODR Filing Ready",
}


def _stage_index(stage: str) -> int:
    return STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0


class SweepRow(CamelModel):
    invoice_id: int
    invoice_number: str
    action: str               # "escalated" | "no_change" | "ineligible"
    from_stage: str | None = None
    to_stage: str
    delivery_status: str | None = None
    source: str | None = None
    skip_reason: str | None = None


class SweepResult(CamelModel):
    processed: int
    escalated: int
    skipped_ineligible: int
    results: list[SweepRow]


@router.post("/escalation/run", response_model=SweepResult)
def run_sweep(db: Session = Depends(get_db)):
    rows = db.execute(select(Invoice, Buyer).join(Buyer)).all()
    results: list[SweepRow] = []
    escalated = 0
    skipped_ineligible = 0

    for inv, buyer in rows:
        stored = inv.escalation_stage or "none"
        computed = get_escalation_stage(inv.invoice_date)

        # Silpi Industries guardrail: skip if Udyam registration postdates invoice.
        if not is_eligible(inv.invoice_date, buyer.udyam_date):
            skipped_ineligible += 1
            results.append(SweepRow(
                invoice_id=inv.id, invoice_number=inv.invoice_number,
                action="ineligible", from_stage=stored, to_stage=stored,
                skip_reason="Udyam registration postdates invoice (Silpi Industries SC 2021)",
            ))
            continue

        # Only act if the invoice has genuinely advanced to a higher stage.
        if computed == "none" or _stage_index(computed) <= _stage_index(stored):
            results.append(SweepRow(
                invoice_id=inv.id, invoice_number=inv.invoice_number,
                action="no_change", from_stage=stored, to_stage=stored,
            ))
            continue

        amount = float(inv.amount)
        language = buyer.language or "English"
        calc = calculate_interest(amount, inv.invoice_date)

        message, source = draft_message(
            stage=computed, buyer_name=buyer.name, invoice_number=inv.invoice_number,
            amount=amount, interest=calc["totalInterest"], total_due=calc["totalDue"],
            days_overdue=calc["msmedDaysOverdue"],
            rate_pct=round(calc["applicableRate"] * 100, 1),
            flag43bh=calc["section43bhApplies"], language=language,
        )

        _valid_email = lambda a: a if a and "@" in a else None
        recipient = settings.demo_recipient_email or _valid_email(buyer.email)
        if recipient:
            delivery = send_notice(
                to=recipient,
                subject=f"{STAGE_SUBJECT.get(computed, 'Payment Notice')} — Invoice {inv.invoice_number}",
                body=message,
            )
            delivery_status = delivery["status"]
        else:
            delivery_status = "no_email"

        # Log the event. approved_by_owner=False: the sweep is autonomous.
        # (In production you'd gate formal_demand/odr_ready behind owner approval.)
        db.add(EscalationEvent(
            invoice_id=inv.id, stage=computed, message=message,
            channel="email", approved_by_owner=False, language=language,
        ))
        inv.escalation_stage = computed
        inv.status = "escalating"
        db.commit()
        escalated += 1

        results.append(SweepRow(
            invoice_id=inv.id, invoice_number=inv.invoice_number,
            action="escalated", from_stage=stored, to_stage=computed,
            delivery_status=delivery_status, source=source,
        ))

    return SweepResult(processed=len(rows), escalated=escalated,
                       skipped_ineligible=skipped_ineligible, results=results)
