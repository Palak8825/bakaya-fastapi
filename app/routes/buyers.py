"""
Buyers router = buyers.ts. Straightforward CRUD — the simplest router, good to
read right after invoices.py to see the pattern repeat.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer
from ..schemas import BuyerCreate, BuyerOut

router = APIRouter(prefix="/api", tags=["buyers"])


@router.get("/buyers", response_model=list[BuyerOut])
def list_buyers(db: Session = Depends(get_db)):
    return db.execute(select(Buyer)).scalars().all()


@router.get("/buyers/{id}", response_model=BuyerOut)
def get_buyer(id: int, db: Session = Depends(get_db)):
    buyer = db.get(Buyer, id)
    if buyer is None:
        raise HTTPException(404, "Buyer not found")
    return buyer


@router.post("/buyers", response_model=BuyerOut, status_code=status.HTTP_201_CREATED)
def create_buyer(body: BuyerCreate, db: Session = Depends(get_db)):
    buyer = Buyer(
        name=body.name, contact_name=body.contact_name,
        email=body.email, language=body.language,
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.patch("/buyers/{id}", response_model=BuyerOut)
def update_buyer(id: int, body: BuyerCreate, db: Session = Depends(get_db)):
    buyer = db.get(Buyer, id)
    if buyer is None:
        raise HTTPException(404, "Buyer not found")
    buyer.name = body.name
    buyer.contact_name = body.contact_name
    buyer.email = body.email
    buyer.language = body.language
    db.commit()
    db.refresh(buyer)
    return buyer
