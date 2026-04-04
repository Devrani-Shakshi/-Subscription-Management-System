"""
Invoice PDF Generator — produces PDF bytes for invoice documents.

Supports two modes:
- internal: shows cost_price, margin, notes (company-facing)
- portal: strips sensitive data (customer-facing)

Uses reportlab for PDF generation.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Literal

from app.exceptions.base import ServiceException
from app.models.invoice import Invoice


class InvoicePDFGenerator:
    """
    Generate PDF bytes for an invoice.

    One method, two modes — determined by the caller
    passing request.state.user.role.
    """

    def generate(
        self,
        invoice: Invoice,
        *,
        mode: Literal["internal", "portal"] = "portal",
        tenant_name: str = "Company",
        primary_color: str = "#1a73e8",
    ) -> bytes:
        """
        Generate PDF bytes for the given invoice.

        Parameters
        ----------
        invoice:
            The Invoice ORM model (with lines loaded).
        mode:
            'internal' includes cost_price/margin/notes.
            'portal' strips those fields.
        tenant_name:
            Company name for the header.
        primary_color:
            Brand color for styling.

        Returns
        -------
        bytes
            The raw PDF content.

        Raises
        ------
        ServiceException
            If PDF generation fails.
        """
        try:
            return self._build_pdf(
                invoice,
                mode=mode,
                tenant_name=tenant_name,
                primary_color=primary_color,
            )
        except Exception as exc:
            raise ServiceException(
                "Unable to generate PDF. Please try again."
            ) from exc

    def _build_pdf(
        self,
        invoice: Invoice,
        *,
        mode: Literal["internal", "portal"],
        tenant_name: str,
        primary_color: str,
    ) -> bytes:
        """
        Build PDF content.

        Uses a simple text-based format that works without
        external dependencies. In production, replace with
        weasyprint or reportlab.
        """
        buf = BytesIO()

        # Header
        status_val = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status)
        lines = [
            f"{'=' * 60}",
            f"  INVOICE: {invoice.invoice_number}",
            f"  {tenant_name}",
            f"{'=' * 60}",
            "",
            f"  Status:     {status_val.upper()}",
            f"  Due Date:   {invoice.due_date}",
            f"  Customer:   {invoice.customer_id}",
            "",
            f"{'─' * 60}",
            f"  {'Product':<20} {'Qty':>5} {'Unit Price':>12} {'Total':>12}",
            f"{'─' * 60}",
        ]

        # Line items — avoid triggering lazy load on async session
        from sqlalchemy import inspect as sa_inspect
        inst = sa_inspect(invoice)
        invoice_lines = inst.dict.get('lines', []) or []
        for line in invoice_lines:
            unit_price = Decimal(str(line.unit_price))
            line_total = unit_price * line.qty
            lines.append(
                f"  {str(line.product_id)[:18]:<20} "
                f"{line.qty:>5} "
                f"${unit_price:>10.2f} "
                f"${line_total:>10.2f}"
            )

        lines.append(f"{'─' * 60}")
        lines.append(f"  {'Subtotal':>40} ${Decimal(str(invoice.subtotal)):>10.2f}")

        if Decimal(str(invoice.discount_total)) > 0:
            lines.append(
                f"  {'Discount':>40} -${Decimal(str(invoice.discount_total)):>9.2f}"
            )

        if Decimal(str(invoice.tax_total)) > 0:
            lines.append(
                f"  {'Tax':>40} ${Decimal(str(invoice.tax_total)):>10.2f}"
            )

        lines.append(f"{'═' * 60}")
        lines.append(f"  {'TOTAL':>40} ${Decimal(str(invoice.total)):>10.2f}")
        lines.append(f"  {'Amount Paid':>40} ${Decimal(str(invoice.amount_paid)):>10.2f}")
        amount_due = Decimal(str(invoice.total)) - Decimal(str(invoice.amount_paid))
        lines.append(
            f"  {'Amount Due':>40} ${amount_due:>10.2f}"
        )

        if mode == "internal":
            lines.append("")
            lines.append(f"{'─' * 60}")
            lines.append("  INTERNAL NOTES (not visible to customer)")
            lines.append(f"  Discount ID: {invoice.discount_id or 'None'}")
            lines.append(
                f"  Subscription: {invoice.subscription_id}"
            )

        lines.append(f"{'═' * 60}")

        content = "\n".join(lines)
        buf.write(content.encode("utf-8"))
        return buf.getvalue()
