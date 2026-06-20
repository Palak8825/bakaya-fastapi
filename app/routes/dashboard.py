from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice, EscalationEvent
from ..rules import calculate_interest, get_escalation_stage
from ..schemas import CamelModel, OverdueStageOut, ActivityItemOut

router = APIRouter(prefix="/api", tags=["dashboard"])

STAGE_LABELS = {
    "none": "Not yet due",
    "nudge": "Gentle nudge",
    "tax_nudge": "Tax nudge",
    "formal_demand": "Formal demand",
    "odr_ready": "ODR ready",
}


class DashboardSummary(CamelModel):
    total_invoices: int
    total_outstanding: float
    overdue_count: int
    overdue_amount: float
    escalating_count: int
    paid_count: int
    recovered_amount: float
    avg_days_overdue: float
    odr_ready_count: int | None = None


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    invoices = db.execute(select(Invoice)).scalars().all()

    total_outstanding = 0.0
    overdue_amount = 0.0
    overdue_count = 0
    escalating_count = 0
    paid_count = 0
    recovered_amount = 0.0
    odr_ready_count = 0
    days_list: list[int] = []

    for inv in invoices:
        amount = float(inv.amount)
        calc = calculate_interest(amount, inv.invoice_date)
        days = calc["msmedDaysOverdue"]

        if inv.status == "paid":
            paid_count += 1
            recovered_amount += amount
            continue

        total_outstanding += amount + calc["totalInterest"]

        if days > 0:
            overdue_count += 1
            overdue_amount += amount
            days_list.append(days)

        if inv.status == "escalating":
            escalating_count += 1

        if inv.escalation_stage == "odr_ready":
            odr_ready_count += 1

    avg_days = round(sum(days_list) / len(days_list), 1) if days_list else 0.0

    return DashboardSummary(
        total_invoices=len(invoices),
        total_outstanding=round(total_outstanding, 2),
        overdue_count=overdue_count,
        overdue_amount=round(overdue_amount, 2),
        escalating_count=escalating_count,
        paid_count=paid_count,
        recovered_amount=round(recovered_amount, 2),
        avg_days_overdue=avg_days,
        odr_ready_count=odr_ready_count,
    )


STAGE_ORDER = ["none", "nudge", "tax_nudge", "formal_demand", "odr_ready"]


@router.get("/dashboard/overdue-breakdown", response_model=list[OverdueStageOut])
def overdue_breakdown(db: Session = Depends(get_db)):
    invoices = db.execute(select(Invoice)).scalars().all()
    stage_count: dict[str, int] = defaultdict(int)
    stage_amount: dict[str, float] = defaultdict(float)

    for inv in invoices:
        if inv.status == "paid":
            continue
        stage = inv.escalation_stage or "none"
        stage_count[stage] += 1
        stage_amount[stage] += float(inv.amount)

    return [
        OverdueStageOut(
            stage=stage,
            count=stage_count[stage],
            amount=round(stage_amount[stage], 2),
            label=STAGE_LABELS.get(stage, stage),
        )
        for stage in STAGE_ORDER
        if stage in stage_count
    ]


@router.get("/dashboard/recent-activity", response_model=list[ActivityItemOut])
def recent_activity(db: Session = Depends(get_db)):
    rows = db.execute(
        select(EscalationEvent, Invoice, Buyer)
        .join(Invoice, EscalationEvent.invoice_id == Invoice.id)
        .join(Buyer, Invoice.buyer_id == Buyer.id)
        .order_by(EscalationEvent.sent_at.desc())
        .limit(20)
    ).all()

    return [
        ActivityItemOut(
            id=event.id,
            invoice_id=event.invoice_id,
            invoice_number=invoice.invoice_number,
            buyer_name=buyer.name,
            stage=event.stage,
            message=event.message,
            sent_at=event.sent_at,
            channel=event.channel,
        )
        for event, invoice, buyer in rows
    ]
