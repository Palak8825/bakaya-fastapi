"""
SQLAlchemy models = your Drizzle schema files (buyers.ts, invoices.ts,
escalation_events.ts), expressed in Python.

Mapping to keep in your head:
    Drizzle                          SQLAlchemy
    -------                          ----------
    pgTable("buyers", {...})    →    class Buyer(Base): __tablename__ = "buyers"
    serial().primaryKey()       →    Column(Integer, primary_key=True)
    text("name").notNull()      →    Column(String, nullable=False)
    text("email")               →    Column(String, nullable=True)
    numeric("amount")           →    Column(Numeric)  (comes back as Decimal)
    date("invoice_date")        →    Column(Date)
    .references(() => buyers.id) →   ForeignKey("buyers.id")

The TABLE STRUCTURE is identical to your TS app — same columns, same types.
Only the declaration syntax differs. If you point DATABASE_URL at the same
Postgres, these models describe the very same tables.
"""
from datetime import date, datetime
from sqlalchemy import (
    Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Equivalent to Drizzle's schema registry — all models inherit from this."""
    pass


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String, default="en")
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    udyam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="buyer")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    escalation_stage: Mapped[str] = mapped_column(String, default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    buyer: Mapped["Buyer"] = relationship(back_populates="invoices")


class EscalationEvent(Base):
    __tablename__ = "escalation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, default="email")
    approved_by_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String, default="en")
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
