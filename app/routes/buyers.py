"""
Buyers router — CRUD + computed totalOutstanding and invoiceCount per buyer.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice
from ..schemas import BuyerCreate, BuyerOut

router = APIRouter(prefix="/api", tags=["buyers"])


def _with_stats(buyer: Buyer, db: Session) -> BuyerOut:
    """Attach totalOutstanding and invoiceCount computed from live invoices."""
    rows = db.execute(
        select(Invoice.amount, Invoice.status)
        .where(Invoice.buyer_id == buyer.id)
    ).all()
    invoice_count = len(rows)
    total_outstanding = sum(
        float(r.amount) for r in rows if r.status != "paid"
    )
    data = BuyerOut.model_validate(buyer)
    data.total_outstanding = total_outstanding
    data.invoice_count = invoice_count
    return data


@router.get("/buyers", response_model=list[BuyerOut])
def list_buyers(db: Session = Depends(get_db)):
    buyers = db.execute(select(Buyer)).scalars().all()
    return [_with_stats(b, db) for b in buyers]


@router.get("/buyers/{id}", response_model=BuyerOut)
def get_buyer(id: int, db: Session = Depends(get_db)):
    buyer = db.get(Buyer, id)
    if buyer is None:
        raise HTTPException(404, "Buyer not found")
    return _with_stats(buyer, db)


@router.post("/buyers", response_model=BuyerOut, status_code=status.HTTP_201_CREATED)
def create_buyer(body: BuyerCreate, db: Session = Depends(get_db)):
    buyer = Buyer(
        name=body.name, contact_name=body.contact_name,
        email=body.email, language=body.language,
        phone=body.phone, gst_number=body.gst_number, city=body.city,
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return _with_stats(buyer, db)


@router.patch("/buyers/{id}", response_model=BuyerOut)
def update_buyer(id: int, body: BuyerCreate, db: Session = Depends(get_db)):
    buyer = db.get(Buyer, id)
    if buyer is None:
        raise HTTPException(404, "Buyer not found")
    buyer.name = body.name
    buyer.contact_name = body.contact_name
    buyer.email = body.email
    buyer.language = body.language
    buyer.phone = body.phone
    buyer.gst_number = body.gst_number
    buyer.city = body.city
    db.commit()
    db.refresh(buyer)
    return _with_stats(buyer, db)
