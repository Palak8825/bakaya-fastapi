"""
Run: python generate_submission_pdf.py
Outputs: Bakaya_TheEdgeCases_InnovateZ2026.pdf
"""
from fpdf import FPDF
from datetime import date

ORANGE = (211, 84, 0)
NAVY   = (13, 43, 84)
WHITE  = (255, 255, 255)
LIGHT  = (245, 246, 248)
DARK   = (30, 30, 30)

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    # ── header ──────────────────────────────────────────────────────────────
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 14, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*ORANGE)
        self.set_xy(10, 3)
        self.cell(0, 8, "Bakaya AI  |  InnovateZ 2026  |  Team: The Edge Cases", align="L")
        self.set_text_color(*WHITE)
        self.set_xy(-40, 3)
        self.cell(30, 8, f"Page {self.page_no()}", align="R")
        self.ln(4)

    # ── footer ──────────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, "BITS Pilani, Hyderabad Campus  -  CS 2nd Year  -  Confidential submission", align="C")

    # ── helpers ─────────────────────────────────────────────────────────────
    def section_title(self, number, title):
        self.ln(4)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, f"  {number}.  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(*DARK)
        self.ln(2)

    def sub(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ORANGE)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*DARK)

    def body(self, text, indent=0):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*DARK)
        self.set_x(self.l_margin + indent)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text, indent=4):
        self.set_font("Helvetica", "", 9.5)
        self.set_x(self.l_margin + indent)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, f"*  {text}")

    def kv(self, label, value, label_w=55):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*NAVY)
        self.cell(label_w, 6, label)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6, value)

    def stat_box(self, items):
        """items = list of (value, label) tuples"""
        self.ln(2)
        box_w = (self.epw) / len(items)
        x0 = self.l_margin
        for val, lbl in items:
            self.set_xy(x0, self.get_y())
            self.set_fill_color(*NAVY)
            self.rect(x0, self.get_y(), box_w - 3, 18, "F")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*ORANGE)
            self.set_xy(x0 + 2, self.get_y() + 1)
            self.cell(box_w - 5, 8, val, align="C")
            self.set_font("Helvetica", "", 7.5)
            self.set_text_color(*WHITE)
            self.set_xy(x0 + 2, self.get_y() + 8)
            self.cell(box_w - 5, 5, lbl, align="C")
            x0 += box_w
        self.ln(22)
        self.set_text_color(*DARK)

    def table(self, headers, rows, col_widths=None):
        self.ln(2)
        usable = self.epw
        if col_widths is None:
            col_widths = [usable / len(headers)] * len(headers)
        # header row
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8.5)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, f"  {h}", border=0, fill=True)
        self.ln()
        # data rows
        for ri, row in enumerate(rows):
            fill = ri % 2 == 0
            self.set_fill_color(*LIGHT)
            self.set_text_color(*DARK)
            self.set_font("Helvetica", "", 8.5)
            # figure out max height for this row
            row_h = 6
            x0 = self.l_margin
            y0 = self.get_y()
            for i, cell in enumerate(row):
                self.set_xy(x0, y0)
                if fill:
                    self.set_fill_color(*LIGHT)
                    self.rect(x0, y0, col_widths[i], row_h, "F")
                self.set_xy(x0 + 1, y0)
                self.multi_cell(col_widths[i] - 2, row_h, str(cell))
                x0 += col_widths[i]
            self.set_y(y0 + row_h)
        self.ln(3)
        self.set_text_color(*DARK)

    def code_block(self, lines):
        self.ln(2)
        self.set_fill_color(235, 237, 240)
        self.set_font("Courier", "", 7.5)
        self.set_text_color(30, 30, 30)
        for line in lines:
            self.set_x(self.l_margin)
            self.cell(0, 4.8, line, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*DARK)

    def cover_page(self):
        # navy top band
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 80, "F")
        # orange accent bar
        self.set_fill_color(*ORANGE)
        self.rect(0, 80, 210, 4, "F")

        self.set_xy(18, 18)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*ORANGE)
        self.cell(0, 12, "Bakaya AI", new_x="LMARGIN", new_y="NEXT")
        self.set_x(18)
        self.set_font("Helvetica", "", 13)
        self.set_text_color(*WHITE)
        self.cell(0, 7, "MSME Accounts-Receivable Desk", new_x="LMARGIN", new_y="NEXT")
        self.set_x(18)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 200, 230)
        self.cell(0, 6, "InnovateZ 2026  -  Round 2 Submission PDF", new_x="LMARGIN", new_y="NEXT")

        # meta block
        self.set_xy(18, 92)
        self.set_text_color(*DARK)
        meta = [
            ("Team", "The Edge Cases"),
            ("College", "BITS Pilani, Hyderabad Campus"),
            ("Branch / Year", "Computer Science - 2nd Year"),
            ("Date", date.today().strftime("%d %B %Y")),
            ("Stack", "React - FastAPI - PostgreSQL - Groq (llama-3.3-70b) - fpdf2"),
            ("Live Demo", "Vercel frontend -> Replit FastAPI backend"),
        ]
        for label, value in meta:
            self.set_x(18)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*NAVY)
            self.cell(45, 7, label)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*DARK)
            self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

        self.set_xy(18, 175)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 5.5,
            "\"Large firms run dedicated accounts-receivable desks to chase payments and protect cash flow.\n"
            "Bakaya gives that same capability to MSMEs that cannot afford one.\"\n\n"
            "The real blocker is fear, not process -- so the desk chases, never the owner.\n"
            "And the buyer's cost of stalling just changed."
        )


# ============================================================
# BUILD
# ============================================================
pdf = PDF()
pdf.set_title("Bakaya AI -- InnovateZ 2026 Submission")
pdf.set_author("The Edge Cases -- BITS Pilani Hyderabad")

# ── COVER ────────────────────────────────────────────────────
pdf.add_page()
pdf.cover_page()


# ── SECTION 1: PROBLEM AND USER FLOW ─────────────────────────
pdf.add_page()
pdf.section_title("1", "Problem and User Flow")

pdf.sub("The Problem")
pdf.body(
    "Large firms run dedicated accounts-receivable desks to chase payments and protect cash flow. "
    "MSMEs cannot afford one -- so the owner does it personally, and then stops doing it to "
    "protect the relationship. The primary barrier to recovery is relationship friction, not workflow "
    "complexity. Working capital stays stuck for months while the owner avoids the conversation."
)

pdf.stat_box([
    ("Rs.22,000 Cr+", "delayed payments visible"),
    ("176 days", "avg. payment wait"),
    ("45 days", "statutory legal limit"),
    ("3-4 Cr", "addressable MSMEs"),
])

pdf.body(
    "Research estimates India's MSME sector holds Rs.10-15 lakh crore in B2B receivables "
    "outstanding beyond 45 days annually. Recovering even 1% would unlock Rs.10,000+ crore in "
    "working capital. Bakaya charges a 2-5% facilitation fee on recovered amounts -- a "
    "Rs.200-500 crore revenue opportunity at modest penetration."
)

pdf.sub("User Flow")
pdf.bullet("Supplier registers, adds buyer and invoice details (manual entry or import from Tally/Zoho/Vyapar).")
pdf.bullet("Dashboard shows live overdue days, accrued statutory interest, and current escalation stage per invoice.")
pdf.bullet("Supplier clicks Send Notice -- an LLM-drafted, stage-appropriate reminder is emailed in the trade language.")
pdf.bullet("Autonomous sweep (POST /api/escalation/run) scans the entire book, advances every invoice that has aged past a threshold, drafts and sends the correct notice, and logs the event -- with no manual intervention.")
pdf.bullet("For invoices aged past 90 days, the supplier downloads a one-click ODR filing pack PDF ready to upload to odr.msme.gov.in.")
pdf.ln(3)

pdf.sub("The Escalation Ladder -- Worked Example")
pdf.body("Context: Selvam runs a Tirupur garment unit. A buyer owes Rs.1.8L past the 45-day mark.")
pdf.ln(1)

stages = [
    ("Day 0",   "Eligibility Check",        "Bakaya matches invoice dates against Selvam's Udyam registration to confirm the MSMED clock applies (Silpi Industries SC 2021 rule)."),
    ("Day 30",  "Relationship-Safe Nudge",  "A polite reminder in Tamil, sent under the business name -- not Selvam's own. No mention of interest or legal action yet."),
    ("Day 46",  "The Tax Nudge",            "Statutory interest starts accruing. Bakaya flags the Section 43B(h) tax cost: this amount is NOT deductible until paid. Buyer now has a financial incentive to settle."),
    ("Day 75",  "Formal Demand",            "Bakaya drafts a formal demand notice with exact principal + compound interest at 3x RBI Bank Rate. Tone: firm and professional."),
    ("Day 90+", "ODR Preparation",          "Full filing pack assembled: purchase orders, delivery logs, interest workings -> ready to submit to odr.msme.gov.in."),
]
pdf.table(
    ["Day", "Stage", "What Bakaya Does"],
    stages,
    col_widths=[20, 45, 107],
)

pdf.body(
    "Why the escalation is credible: Filing at the MSME Facilitation Council is free for the supplier - "
    "the council must rule within 90 days - buyers must deposit 75% of any award to appeal -- "
    "so they cannot simply stall."
)


# ── SECTION 2: UNDER-THE-HOOD DESIGN ─────────────────────────
pdf.add_page()
pdf.section_title("2", "Under-the-Hood Design")

pdf.sub("Data Flow -- Autonomous Escalation Sweep")
pdf.code_block([
    "POST /api/escalation/run",
    "  |",
    "  +-- DB: load all (Invoice JOIN Buyer)",
    "  |",
    "  +-- rules.py: get_escalation_stage(invoice_date)",
    "  |     5-stage ladder: none -> nudge -> tax_nudge -> formal_demand -> odr_ready",
    "  |     Thresholds: 30 / 46 / 75 / 90 days since invoice date",
    "  |     Pure date arithmetic -- no network, no LLM",
    "  |",
    "  +-- rules.py: calculate_interest(amount, invoice_date)",
    "  |     Rate   = 3 x RBI Bank Rate = 16.5% p.a. (June 2026)",
    "  |     Method = compound, monthly rests, starting day 46",
    "  |     Returns: { principal, totalInterest, totalDue,",
    "  |                msmedDaysOverdue, applicableRate, section43bhApplies }",
    "  |     All Decimal -- no float rounding errors in legal amounts",
    "  |",
    "  +-- Stage-index guard (idempotency)",
    "  |     Only acts if computed_stage_index > stored_stage_index",
    "  |     Re-running the sweep never re-sends the same notice",
    "  |",
    "  +-- drafting.py: draft_message(stage, buyer_name, numbers, language)",
    "  |     Primary:  Groq API -> llama-3.3-70b-versatile",
    "  |               Prompt injects pre-computed numbers; LLM writes tone only",
    "  |               Tone: warm nudge -> tax alert -> formal -> final notice",
    "  |     Fallback: deterministic template (no API key needed; always works)",
    "  |",
    "  +-- notify.py: send_notice(to, subject, body)",
    "  |     EMAIL_MODE=real       -> Gmail SMTP (smtplib)",
    "  |     EMAIL_MODE=simulation -> console log (safe for demos)",
    "  |",
    "  +-- DB: write EscalationEvent, advance invoice.escalation_stage, commit",
])

pdf.sub("ODR PDF Generation")
pdf.body(
    "GET /api/invoices/{id}/odr-pack builds a downloadable PDF (fpdf2) containing: parties, invoice "
    "summary, full MSMED s.16 interest workings (rate, months, total), escalation timeline, a "
    "ready-to-file claim statement citing MSMED Act ss.15-17, document checklist (Udyam cert, "
    "PO, delivery proof, bank statement), and a recovery priority flag (HIGH / MEDIUM / LOW)."
)

pdf.sub("Key Design Decisions")
pdf.bullet("LLM's role is constrained to tone and language only. All numbers (interest, days overdue, total due) are computed deterministically by rules.py and injected into the prompt. The model never computes a figure.")
pdf.bullet("The stage-index guard makes the sweep idempotent. _stage_index(computed) > _stage_index(stored) is the only condition under which an action is taken. Re-running at any time is safe.")
pdf.bullet("Decimal arithmetic throughout calculate_interest() avoids float rounding errors in legal financial amounts.")
pdf.bullet("Template fallback in drafting.py means a draft is always produced -- Groq API key is optional, the app works without it.")


# ── SECTION 3: DATA SOURCES ───────────────────────────────────
pdf.add_page()
pdf.section_title("3", "Data Sources and References")

pdf.table(
    ["Source", "Role in the System"],
    [
        ("MSMED Act 2006, ss.15-17",         "45-day payment limit; compound interest entitlement; ODR filing right"),
        ("RBI Bank Rate 5.5% (June 2026)",        "STATUTORY_RATE = 3 x Bank Rate = 16.5% p.a. -- hardcoded in rules.py"),
        ("Income Tax Act, s.43B(h)",              "Buyer deductibility flag -- buyer cannot deduct until actually paid"),
        ("Silpi Industries v. Kerala SRTC (SC 2021)", "Eligibility guardrail: Udyam registration must predate the invoice"),
        ("MSME ODR Portal (odr.msme.gov.in)",     "Filing destination referenced in the ODR pack PDF and claim statement"),
        ("Groq API (llama-3.3-70b-versatile)",    "LLM for drafting notice text -- tone and language only; never computes figures"),
        ("SQLite / PostgreSQL (Neon)",            "Buyer, invoice, and escalation-event storage"),
        ("seed.py mock data",                     "3 sample invoices across 3 buyers for zero-setup demo"),
        ("MSME Ministry data (Feb 2026)",         "~3-4 crore addressable businesses; market sizing"),
    ],
    col_widths=[70, 102],
)

pdf.sub("How sources influence the output")
pdf.body(
    "The MSMED Act and RBI Bank Rate together determine every financial figure the system produces. "
    "The Silpi Industries ruling gates the entire pipeline -- if Udyam registration postdates the "
    "invoice, no escalation is triggered and no interest is claimed. Section 43B(h) controls whether "
    "the tax-nudge paragraph appears in a notice. The Groq LLM only receives the output of these "
    "legal computations; it cannot alter them."
)


# ── SECTION 4: VALUE BEYOND A GENERIC LLM ────────────────────
pdf.add_page()
pdf.section_title("4", "Value Beyond a Generic LLM")

pdf.body(
    "A user cannot get the same result from ChatGPT, Claude, or Gemini because these tools have no "
    "state, no deterministic legal maths, no idempotency, and no ability to autonomously walk an "
    "entire invoice book and take action."
)

pdf.table(
    ["Capability", "Bakaya", "Generic LLM"],
    [
        ("Statutory interest maths",
         "Deterministic compound calculation at 3x RBI Bank Rate, monthly rests, from day 46 -- auditable",
         "Unreliable; LLMs hallucinate financial figures"),
        ("Stage-aware escalation",
         "5-stage state machine with date-driven thresholds; stage-index guard prevents duplicate sends",
         "No state; no idempotency"),
        ("Udyam eligibility check",
         "Validates registration predates invoice (Silpi Industries SC 2021)",
         "No domain guardrail"),
        ("Autonomous book sweep",
         "One API call walks every overdue invoice, drafts, sends, logs, and advances stage",
         "Manual; one invoice at a time"),
        ("ODR filing pack PDF",
         "Pre-filled, legally structured PDF with interest workings and escalation history",
         "Cannot produce a legally correct, case-specific PDF"),
        ("Section 43B(h) flag",
         "Computed per invoice; included in notices automatically when applicable",
         "No integration with Indian tax law triggers"),
        ("LLM's actual role",
         "Tone and language only -- numbers passed in, never computed by the model",
         "Trusted to compute numbers (hallucination risk)"),
    ],
    col_widths=[45, 80, 47],
)

pdf.sub("Competitive Positioning")
pdf.table(
    ["Alternative", "Gap"],
    [
        ("Vyapar / Khatabook / Zoho",  "Generic reminders -- legally blind; no 45-day clock, no interest tracking, no legal leverage"),
        ("CA & legal recovery firms",  "Upfront fees; engage only after the relationship is already damaged"),
        ("Govt MSME ODR Portal",       "Starts only when a dispute is filed -- nothing covers the 0-90 day pre-dispute window"),
        ("Owner's WhatsApp",      "Solves nothing; the fear of damaging the relationship is the real blocker"),
    ],
    col_widths=[55, 117],
)

pdf.body(
    "Bakaya's edge: Pre-dispute automation capturing the overlooked 0-90 day window - "
    "depersonalised chasing (the AR desk effect) - per-invoice legal layer no app has - "
    "vernacular-first notices in the language the trade actually runs in."
)


# ── SECTION 5: ARCHITECTURE ───────────────────────────────────
pdf.add_page()
pdf.section_title("5", "Architecture and Technical Design")

pdf.code_block([
    "+--------------------------------------------------------------+",
    "|               React Frontend (Vercel)                        |",
    "|     Vite + TanStack Query + Wouter + shadcn/ui               |",
    "+------------------------+-------------------------------------+",
    "                         |  JSON (camelCase, same contract)",
    "                         |  /api/* rewrites via vercel.json",
    "+------------------------v-------------------------------------+",
    "|              FastAPI  (Python 3.12 -- Replit)                |",
    "|                                                              |",
    "|  /buyers   /invoices   /dashboard  /escalation  /odr-pack   |",
    "|                                                              |",
    "|  +-------------+  +--------------+  +------------------+    |",
    "|  |  rules.py   |  | drafting.py  |  |   notify.py      |    |",
    "|  | MSMED law   |  | Groq / tmpl  |  | SMTP / sim.      |    |",
    "|  | pure maths  |  | tone only    |  |                  |    |",
    "|  +-------------+  +--------------+  +------------------+    |",
    "|                                                              |",
    "|  +--------------------------------------------------+        |",
    "|  |        SQLAlchemy ORM                            |        |",
    "|  |   Buyer  .  Invoice  .  EscalationEvent         |        |",
    "|  +------------------+---------------------------------+       |",
    "+---------------------|-----------------------------------------+",
    "                      |",
    "          +-----------+-----------+",
    "          |  SQLite (dev/demo)    |",
    "          |  PostgreSQL / Neon    |",
    "          |    (production)       |",
    "          +----------+------------+",
    "",
    "External services",
    "  Groq API  ->  llama-3.3-70b-versatile  (LLM drafting; optional)",
    "  Gmail SMTP                              (real email mode; optional)",
    "  odr.msme.gov.in                         (manual upload target for ODR pack)",
    "",
    "Planned (not yet wired in MVP)",
    "  Bhashini API         ->  vernacular translation (Tamil, Hindi, Marathi...)",
    "  WhatsApp Business API ->  outbound delivery channel",
    "  Tally / Zoho / Vyapar ->  invoice import integrations",
])

pdf.sub("Key Technical Points")
pdf.bullet("Same JSON contract (camelCase via Pydantic aliasing) as the TypeScript/Express version -- the Vercel frontend works against both backends unchanged.")
pdf.bullet("vercel.json rewrites all /api/* traffic to the Replit backend URL, so the frontend is a pure static build with no backend coupling.")
pdf.bullet("SQLite is the default for zero-setup demo; DATABASE_URL can be switched to PostgreSQL/Neon for production.")
pdf.bullet("Auto-generated OpenAPI docs at /docs (from Pydantic models) -- no hand-maintained spec.")


# ── SECTION 6: DEMO SCENARIO AND LIMITATIONS ─────────────────
pdf.add_page()
pdf.section_title("6", "Demo Scenario and Limitations")

pdf.sub("Scenario A -- Autonomous Sweep on a Stale Invoice Book")
pdf.body("Input: Three seed invoices all dated > 90 days ago (populated by python seed.py).")
pdf.ln(1)

pdf.code_block([
    "# Step 1 -- populate the database",
    "python seed.py",
    "",
    "# Step 2 -- run the autonomous sweep",
    "curl -X POST https://bakaya-fastapi--Palak8825.replit.app/api/escalation/run",
    "",
    "# Response",
    '{',
    '  "processed": 3,',
    '  "escalated": 3,',
    '  "results": [',
    '    {',
    '      "invoiceId": 1,',
    '      "invoiceNumber": "INV-001",',
    '      "action": "escalated",',
    '      "fromStage": "none",',
    '      "toStage": "odr_ready",',
    '      "deliveryStatus": "simulated",',
    '      "source": "llm"',
    '    }',
    '  ]',
    '}',
])

pdf.body(
    "What happened: rules.py computed odr_ready for all three (age > 90 days). Stage-index guard "
    "confirmed stored stage was none. drafting.py called Groq and produced a final-notice draft. "
    "notify.py logged to console (simulation mode). Three EscalationEvent rows written; all invoices "
    "advanced to odr_ready. Re-running the sweep produces zero escalations -- idempotency confirmed."
)

pdf.sub("Scenario B -- ODR Filing Pack PDF")
pdf.code_block([
    "curl https://bakaya-fastapi--Palak8825.replit.app/api/invoices/1/odr-pack -o ODR-Pack-INV-001.pdf",
])
pdf.body(
    "Output: A downloadable PDF containing -- parties and invoice details, MSMED s.16 interest "
    "workings (principal, rate, months, total), escalation timeline with dates and channels, "
    "claim statement citing MSMED Act ss.15-17, document checklist, and a recovery priority flag."
)

pdf.sub("Build Status")
pdf.table(
    ["Feature", "Status"],
    [
        ("Buyer CRUD",                                  "Working"),
        ("Invoice create / list with live interest",    "Working"),
        ("Escalation sweep (autonomous)",               "Working"),
        ("LLM drafting via Groq",                       "Working (template fallback if no API key)"),
        ("Email -- simulation mode",                "Working"),
        ("Email -- real Gmail SMTP",                "Working"),
        ("ODR filing pack PDF",                         "Working"),
        ("Dashboard aggregate metrics",                 "Working"),
        ("Udyam eligibility date check",               "Implemented in rules.py; not yet wired to the UI"),
        ("Owner-approval gate (formal_demand / odr_ready)", "Deliberate MVP scope: sweep is autonomous. Production build will gate these two stages behind a one-tap owner confirmation screen before any notice is sent."),
        ("Alembic migrations",                          "Not yet -- init_db() is dev-only; production needs Alembic"),
        ("Bhashini vernacular translation",             "Planned; language field on Buyer model exists"),
        ("WhatsApp Business API delivery",              "Planned; email is the current delivery channel"),
        ("Tally / Zoho / Vyapar import",                "Planned; manual entry only in MVP"),
    ],
    col_widths=[80, 92],
)


# ── OUTPUT ────────────────────────────────────────────────────
out = "Bakaya_TheEdgeCases_InnovateZ2026.pdf"
pdf.output(out)
print(f"PDF written to: {out}")
