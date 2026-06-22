"""
Pydantic schemas = your Zod schemas. Two jobs:

1. INPUT validation: declare a model as a route argument and FastAPI validates
   the request body automatically (bad input → 422), no manual checks.

2. OUTPUT shaping: snake_case in Python, camelCase in JSON — the frontend sees
   byte-identical keys to the TS API and needs zero changes.
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base: snake_case in Python, camelCase in JSON."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ---- Input bodies ----

class BuyerCreate(CamelModel):
    name: str
    contact_name: str | None = None
    email: str | None = None
    language: str = "en"
    phone: str | None = None
    gst_number: str | None = None
    city: str | None = None
    udyam_date: date | None = None


class InvoiceCreate(CamelModel):
    buyer_id: int
    invoice_number: str
    amount: float
    invoice_date: date
    due_date: date | None = None
    description: str | None = None
    po_number: str | None = None


class InvoiceUpdate(CamelModel):
    amount: float | None = None
    due_date: date | None = None
    status: str | None = None
    description: str | None = None
    po_number: str | None = None


class EscalationInput(CamelModel):
    stage: str
    channel: str
    approved_by_owner: bool
    custom_message: str | None = None


class SendRequest(CamelModel):
    to: str | None = None
    stage: str | None = None
    language: str | None = None


# ---- Output shapes ----

class BuyerOut(CamelModel):
    id: int
    name: str
    contact_name: str | None = None
    email: str | None = None
    language: str
    phone: str | None = None
    gst_number: str | None = None
    city: str | None = None
    udyam_date: date | None = None
    created_at: datetime | None = None
    total_outstanding: float = 0.0
    invoice_count: int = 0


class InvoiceOut(CamelModel):
    id: int
    buyer_id: int
    invoice_number: str
    amount: float
    invoice_date: date
    due_date: date | None
    status: str
    escalation_stage: str
    days_overdue: int | None = None
    interest_accrued: float | None = None
    buyer_name: str | None = None
    created_at: datetime | None = None
    description: str | None = None
    po_number: str | None = None


class EscalationEventOut(CamelModel):
    id: int
    invoice_id: int
    stage: str
    message: str
    sent_at: datetime
    channel: str
    approved_by_owner: bool
    language: str | None = None


class InvoiceDetailOut(CamelModel):
    id: int
    buyer_id: int
    invoice_number: str
    amount: float
    invoice_date: date
    due_date: date | None
    status: str
    escalation_stage: str
    days_overdue: int | None = None
    interest_accrued: float | None = None
    buyer_name: str | None = None
    created_at: datetime | None = None
    description: str | None = None
    po_number: str | None = None
    escalation_events: list[EscalationEventOut] = []


class InterestCalcOut(CamelModel):
    invoice_id: int
    principal_amount: float
    days_overdue: int
    rbi_rate: float
    applicable_rate: float
    daily_interest: float
    total_interest: float
    total_due: float
    is_legally_overdue: bool
    section_43bh_applies: bool | None = None


class OverdueStageOut(CamelModel):
    stage: str
    count: int
    amount: float
    label: str | None = None


class ActivityItemOut(CamelModel):
    id: int
    invoice_id: int
    invoice_number: str
    buyer_name: str
    stage: str
    message: str
    sent_at: datetime
    channel: str


class SendResult(CamelModel):
    stage: str
    source: str
    message: str
    delivery_status: str
    delivery_detail: str
    recipient: str
