"""
ODR router = odr.ts. Generates a downloadable PDF "filing pack" for an invoice:
the legal summary, interest workings, and escalation history a supplier would
take to the MSME ODR Portal.

TS used pdfkit; Python has no pdfkit, so this uses fpdf2 — same job, different
library. This is the kind of swap you hit in any port: the orchestration is
identical, only the PDF API differs. Returns the PDF as a streamed download.
"""
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice, EscalationEvent
from ..rules import calculate_interest, STATUTORY_RATE, RBI_BANK_RATE

router = APIRouter(prefix="/api", tags=["odr"])


@router.get("/invoices/{id}/odr-pack")
def odr_pack(id: int, db: Session = Depends(get_db)):
    row = db.execute(
        select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)
    ).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row

    events = db.execute(
        select(EscalationEvent)
        .where(EscalationEvent.invoice_id == id)
        .order_by(EscalationEvent.sent_at)
    ).scalars().all()

    amount = float(inv.amount)
    calc = calculate_interest(amount, inv.invoice_date)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MSME ODR Filing Pack", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated {date.today().isoformat()} - via Bakaya", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def section(title):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    def line(label, value):
        pdf.cell(60, 6, label)
        pdf.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")

    section("Parties")
    line("Supplier (claimant):", "MSME Supplier (Udyam-registered)")
    line("Buyer (respondent):", buyer.name)
    line("Buyer contact name:", buyer.contact_name or "(not recorded)")
    line("Buyer email:", buyer.email or "(not recorded)")
    pdf.ln(2)

    section("Invoice")
    line("Invoice number:", inv.invoice_number)
    line("Invoice date:", inv.invoice_date.isoformat())
    line("Principal amount:", f"Rs {amount:,.2f}")
    line("Days overdue (past 45):", calc["msmedDaysOverdue"])
    pdf.ln(2)

    section("Interest workings (MSMED Act s.16)")
    line("RBI Bank Rate:", f"{float(RBI_BANK_RATE) * 100:.2f}%")
    line("Statutory rate (3x):", f"{float(STATUTORY_RATE) * 100:.1f}% p.a. compound, monthly rests")
    line("Interest accrued:", f"Rs {calc['totalInterest']:,.2f}")
    line("Total payable:", f"Rs {calc['totalDue']:,.2f}")
    line("Section 43B(h):", "Applies" if calc["section43bhApplies"] else "Not yet")
    pdf.ln(2)

    section("Escalation history")
    if events:
        for e in events:
            pdf.cell(0, 6, f"- {e.sent_at:%Y-%m-%d}  {e.stage}  (channel: {e.channel})",
                     new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 6, "- No escalation events recorded yet.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    section("Claim statement")
    pdf.multi_cell(0, 5,
        f"The claimant seeks recovery of Rs {amount:,.2f} principal and "
        f"Rs {calc['totalInterest']:,.2f} statutory interest (total Rs {calc['totalDue']:,.2f}) "
        f"under Sections 15-17 of the MSMED Act 2006. Interest accrues at "
        f"{float(STATUTORY_RATE)*100:.1f}% p.a. (three times the RBI Bank Rate) "
        f"compounded monthly from the date of expiry of the 45-day payment period.")
    pdf.ln(4)

    section("Document checklist")
    for item in [
        "Invoice copy",
        "Udyam Registration Certificate (supplier)",
        "Purchase Order / Work Order",
        "Delivery proof (LR / e-way bill / GRN)",
        "Payment reminder emails / escalation records",
        "Bank statement showing non-receipt of payment",
    ]:
        pdf.cell(0, 6, f"[ ]  {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    section("Filing note")
    pdf.multi_cell(0, 5,
        "This pack supports a reference to the MSME Facilitation Council via the "
        "ODR Portal (odr.msme.gov.in) for the above invoice. Figures are computed "
        "under the MSMED Act 2006; the buyer's 43B(h) deduction is contingent on payment.")

    buf = io.BytesIO(pdf.output())
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ODR-Pack-{inv.invoice_number}.pdf"'},
    )
