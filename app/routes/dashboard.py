"""
Dashboard router = dashboard.ts. Computes summary metrics live from the DB by
running every invoice through the rules engine — no stored/duplicated numbers.
"""
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Invoice
from ..rules import calculate_interest, get_escalation_stage
from ..schemas import CamelModel

router = APIRouter(prefix="/api", tags=["dashboard"])


class DashboardSummary(CamelModel):
    total_invoices: int
    total_outstanding: float
    total_interest_accrued: float
    odr_ready_count: int
    stage_breakdown: dict[str, int]


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    invoices = db.execute(select(Invoice)).scalars().all()

    total_outstanding = 0.0
    total_interest = 0.0
    breakdown: dict[str, int] = defaultdict(int)

    for inv in invoices:
        if inv.status == "paid":
            continue
        amount = float(inv.amount)
        calc = calculate_interest(amount, inv.invoice_date)
        stage = get_escalation_stage(inv.invoice_date)
        total_outstanding += amount + calc["totalInterest"]
        total_interest += calc["totalInterest"]
        breakdown[stage] += 1

    return DashboardSummary(
        total_invoices=len(invoices),
        total_outstanding=round(total_outstanding, 2),
        total_interest_accrued=round(total_interest, 2),
        odr_ready_count=breakdown.get("odr_ready", 0),
        stage_breakdown=dict(breakdown),
    )
