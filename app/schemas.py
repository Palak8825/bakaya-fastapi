"""
Pydantic schemas = your Zod schemas. Two jobs:

1. INPUT validation: declare a model as a route argument and FastAPI validates
   the request body automatically (bad input → 422), no manual checks.

2. OUTPUT shaping: this is the critical bit for reusing your React frontend.
   Python writes snake_case (invoice_number); your React hooks expect camelCase
   (invoiceNumber). The `alias_generator=to_camel` + `populate_by_name` config
   makes Pydantic ACCEPT snake_case from your Python objects but EMIT camelCase
   JSON — so the frontend sees byte-identical keys to the TS API and needs zero
   changes. This is the "JSON contract" discipline in action.
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base: snake_case in Python, camelCase in JSON."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,     # still accept snake_case when constructing
        from_attributes=True,      # allow building straight from SQLAlchemy objects
    )


# ---- Input bodies (validation) ----
class BuyerCreate(CamelModel):
    name: str
    contact_name: str | None = None
    email: str | None = None
    language: str = "en"


class InvoiceCreate(CamelModel):
    buyer_id: int
    invoice_number: str
    amount: float
    invoice_date: date
    due_date: date | None = None


class SendRequest(CamelModel):
    to: str | None = None
    stage: str | None = None
    language: str | None = None


# ---- Output shapes ----
class BuyerOut(CamelModel):
    id: int
    name: str
    contact_name: str | None
    email: str | None
    language: str


class InvoiceOut(CamelModel):
    id: int
    buyer_id: int
    invoice_number: str
    amount: float
    invoice_date: date
    due_date: date | None
    status: str
    escalation_stage: str
    # computed fields (added in the route, like the TS app does)
    days_overdue: int | None = None
    interest_accrued: float | None = None
    buyer_name: str | None = None


class SendResult(CamelModel):
    stage: str
    source: str
    message: str
    delivery_status: str
    delivery_detail: str
    recipient: str
