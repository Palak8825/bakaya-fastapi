"""
Unit tests for core pure functions in the Bakaya FastAPI project.
Covers: rules.py, notify.py (send_notice), drafting.py (_template).
No DB, no routes, no network — pure function tests only.
"""
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Make sure the app package is importable when pytest is run from the project
# root (D:\bakaya-Final\bakaya-fastapi).
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ===========================================================================
# rules.py — days_since_invoice
# ===========================================================================
class TestDaysSinceInvoice:
    def test_known_date(self):
        """days_since_invoice with a fixed reference date returns exact delta."""
        from app.rules import days_since_invoice
        invoice = date(2026, 1, 1)
        today   = date(2026, 2, 1)     # exactly 31 days later
        assert days_since_invoice(invoice, today) == 31

    def test_same_day_is_zero(self):
        from app.rules import days_since_invoice
        d = date(2026, 6, 1)
        assert days_since_invoice(d, d) == 0

    def test_one_day(self):
        from app.rules import days_since_invoice
        assert days_since_invoice(date(2026, 6, 1), date(2026, 6, 2)) == 1


# ===========================================================================
# rules.py — get_escalation_stage
# ===========================================================================
class TestGetEscalationStage:
    """
    Thresholds (days since invoice):
      <30  → none
      ≥30  → nudge
      ≥46  → tax_nudge
      ≥75  → formal_demand
      ≥90  → odr_ready
    """

    def _stage(self, days: int) -> str:
        from app.rules import get_escalation_stage
        today   = date(2026, 6, 1)
        invoice = date(today.year, today.month, today.day)
        # subtract days by using a shifted 'today'
        from datetime import timedelta
        return get_escalation_stage(invoice, today + timedelta(days=days))

    def test_day_0(self):
        assert self._stage(0) == "none"

    def test_day_29(self):
        assert self._stage(29) == "none"

    def test_day_30(self):
        assert self._stage(30) == "nudge"

    def test_day_45(self):
        assert self._stage(45) == "nudge"

    def test_day_46(self):
        assert self._stage(46) == "tax_nudge"

    def test_day_74(self):
        assert self._stage(74) == "tax_nudge"

    def test_day_75(self):
        assert self._stage(75) == "formal_demand"

    def test_day_89(self):
        assert self._stage(89) == "formal_demand"

    def test_day_90(self):
        assert self._stage(90) == "odr_ready"

    def test_day_120(self):
        assert self._stage(120) == "odr_ready"


# ===========================================================================
# rules.py — is_eligible
# ===========================================================================
class TestIsEligible:
    def test_udyam_none_returns_false(self):
        from app.rules import is_eligible
        assert is_eligible(date(2026, 1, 1), None) is False

    def test_udyam_after_invoice_returns_false(self):
        """Registered AFTER the invoice was raised → NOT protected."""
        from app.rules import is_eligible
        invoice_date = date(2025, 6, 1)
        udyam_date   = date(2025, 12, 1)   # registered later
        assert is_eligible(invoice_date, udyam_date) is False

    def test_udyam_same_day_as_invoice_returns_false(self):
        """Same day: udyam_date < invoice_date is False."""
        from app.rules import is_eligible
        d = date(2025, 6, 1)
        assert is_eligible(d, d) is False

    def test_udyam_before_invoice_returns_true(self):
        """Registered BEFORE invoice → fully protected under s.16."""
        from app.rules import is_eligible
        invoice_date = date(2025, 12, 1)
        udyam_date   = date(2025, 6, 1)    # registered earlier
        assert is_eligible(invoice_date, udyam_date) is True


# ===========================================================================
# rules.py — calculate_interest
# ===========================================================================
class TestCalculateInterest:
    def test_zero_days_overdue_no_interest(self):
        """Invoice raised today: no interest, no 43B(h) flag."""
        from app.rules import calculate_interest
        today = date(2026, 6, 1)
        result = calculate_interest(10000, today, today)
        assert result["totalInterest"] == 0.0
        assert result["msmedDaysOverdue"] == 0
        assert result["section43bhApplies"] is False

    def test_within_45_days_no_interest(self):
        """44 days elapsed: still within the 45-day window."""
        from app.rules import calculate_interest
        from datetime import timedelta
        invoice = date(2026, 6, 1)
        today   = invoice + timedelta(days=44)
        result  = calculate_interest(10000, invoice, today)
        assert result["totalInterest"] == 0.0
        assert result["section43bhApplies"] is False

    def test_30_days_overdue_accrues_interest(self):
        """30 days past the 45-day limit → some interest > 0."""
        from app.rules import calculate_interest
        from datetime import timedelta
        invoice = date(2026, 1, 1)
        today   = invoice + timedelta(days=45 + 30)   # 75 days total
        result  = calculate_interest(100000, invoice, today)
        assert result["totalInterest"] > 0
        assert result["msmedDaysOverdue"] == 30
        assert result["section43bhApplies"] is True

    def test_section43bh_applies_flag(self):
        """section43bhApplies is True whenever overdue > 0."""
        from app.rules import calculate_interest
        from datetime import timedelta
        invoice = date(2026, 1, 1)
        today   = invoice + timedelta(days=46)   # 1 day overdue
        result  = calculate_interest(50000, invoice, today)
        assert result["section43bhApplies"] is True

    def test_result_keys_present(self):
        """Result dict always contains all expected keys."""
        from app.rules import calculate_interest
        from datetime import timedelta
        invoice = date(2026, 1, 1)
        result  = calculate_interest(10000, invoice, invoice + timedelta(days=60))
        expected_keys = {
            "principal", "totalInterest", "totalDue",
            "msmedDaysOverdue", "applicableRate", "section43bhApplies",
        }
        assert expected_keys.issubset(result.keys())

    def test_applicable_rate_is_3x_bank_rate(self):
        """Statutory rate must be 3× RBI Bank Rate = 0.165."""
        from app.rules import calculate_interest, RBI_BANK_RATE
        from datetime import timedelta
        invoice = date(2026, 1, 1)
        result  = calculate_interest(10000, invoice, invoice + timedelta(days=90))
        assert abs(result["applicableRate"] - float(RBI_BANK_RATE * 3)) < 1e-9

    def test_total_due_equals_principal_plus_interest(self):
        """totalDue == principal + totalInterest (within floating point tolerance)."""
        from app.rules import calculate_interest
        from datetime import timedelta
        invoice = date(2026, 1, 1)
        result  = calculate_interest(75000, invoice, invoice + timedelta(days=100))
        assert abs(result["totalDue"] - (result["principal"] + result["totalInterest"])) < 0.02


# ===========================================================================
# notify.py — send_notice
# ===========================================================================
class TestSendNotice:
    """Tests that do NOT touch SMTP — pure function-level checks."""

    def test_no_at_sign_returns_failed(self):
        """Address without '@' must immediately return status=failed."""
        from app.notify import send_notice
        result = send_notice("notanemail", "Subject", "Body")
        assert result["status"] == "failed"
        assert "Invalid" in result["detail"] or "invalid" in result["detail"].lower()

    def test_empty_address_returns_failed(self):
        from app.notify import send_notice
        result = send_notice("", "Subject", "Body")
        assert result["status"] == "failed"

    def test_whitespace_only_address_returns_failed(self):
        from app.notify import send_notice
        result = send_notice("   ", "Subject", "Body")
        assert result["status"] == "failed"

    def test_simulation_mode_returns_simulated(self):
        """When email_mode == 'simulation', a valid address must return status=simulated.

        The .env in this project sets EMAIL_MODE=real with live GMAIL creds, so we
        must patch settings here (just as we do in every other notify test) to avoid
        actually triggering SMTP.
        """
        from app import notify
        mock_settings = MagicMock()
        mock_settings.email_mode = "simulation"
        mock_settings.gmail_address = None
        mock_settings.gmail_app_password = None
        with patch.object(notify, "settings", mock_settings):
            result = notify.send_notice("buyer@example.com", "Due: INV-001", "Please pay.")
        assert result["status"] == "simulated"
        assert "simulated" in result["detail"].lower() or "Simulated" in result["detail"]

    def test_simulation_mode_explicit_patch(self):
        """Patch settings to explicitly verify simulation branch."""
        from app import notify
        mock_settings = MagicMock()
        mock_settings.email_mode = "simulation"
        mock_settings.gmail_address = None
        mock_settings.gmail_app_password = None
        with patch.object(notify, "settings", mock_settings):
            result = notify.send_notice("test@example.com", "Hi", "Body")
        assert result["status"] == "simulated"

    def test_real_mode_no_creds_still_simulated(self):
        """email_mode='real' but missing creds → simulated (safe fallback)."""
        from app import notify
        mock_settings = MagicMock()
        mock_settings.email_mode = "real"
        mock_settings.gmail_address = ""         # empty = falsy
        mock_settings.gmail_app_password = ""
        with patch.object(notify, "settings", mock_settings):
            result = notify.send_notice("test@example.com", "Hi", "Body")
        assert result["status"] == "simulated"


# ===========================================================================
# drafting.py — _template (deterministic fallback)
# ===========================================================================
class TestTemplate:
    """_template() is pure and deterministic — no LLM, no network."""

    def _call(self, **kwargs):
        from app.drafting import _template
        defaults = dict(
            stage="nudge",
            buyer_name="Acme Corp",
            invoice_number="INV-042",
            amount=50000,
            interest=0,
            total_due=50000,
            days_overdue=10,
            flag43bh=False,
        )
        defaults.update(kwargs)
        return _template(**defaults)

    def test_contains_buyer_name(self):
        result = self._call(buyer_name="Acme Corp")
        assert "Acme Corp" in result

    def test_contains_invoice_number(self):
        result = self._call(invoice_number="INV-042")
        assert "INV-042" in result

    def test_contains_amount(self):
        """Amount 50,000 should appear formatted with a comma."""
        result = self._call(amount=50000)
        assert "50,000" in result

    def test_no_interest_line_when_interest_zero(self):
        result = self._call(interest=0)
        assert "Interest" not in result or "Interest of Rs 0" not in result

    def test_interest_line_present_when_interest_positive(self):
        result = self._call(interest=1500, total_due=51500)
        assert "1,500" in result       # interest amount
        assert "51,500" in result      # total due

    def test_43bh_line_present_when_flag_true(self):
        result = self._call(flag43bh=True)
        assert "43B(h)" in result

    def test_43bh_line_absent_when_flag_false(self):
        result = self._call(flag43bh=False)
        assert "43B(h)" not in result

    def test_sign_off_present(self):
        result = self._call()
        assert "Accounts Desk" in result

    def test_days_overdue_in_output(self):
        result = self._call(days_overdue=17)
        assert "17" in result

    def test_returns_string(self):
        result = self._call()
        assert isinstance(result, str)
        assert len(result) > 10
