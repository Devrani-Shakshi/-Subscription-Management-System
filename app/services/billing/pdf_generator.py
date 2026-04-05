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
        Uses reportlab to generate an actual binary PDF.
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        width, height = letter

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(primary_color)
        c.drawString(50, height - 50, tenant_name)
        
        c.setFillColor("black")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 75, f"INVOICE: {invoice.invoice_number}")
        
        status_val = invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status)
        c.drawString(50, height - 95, f"Status: {status_val.upper()}")
        c.drawString(50, height - 110, f"Due Date: {invoice.due_date}")
        c.drawString(50, height - 125, f"Customer ID: {str(invoice.customer_id)}")

        y = height - 170

        # Table Header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Product / Description")
        c.drawString(300, y, "Qty")
        c.drawString(380, y, "Unit Price")
        c.drawString(480, y, "Total")
        y -= 10
        c.setLineWidth(1)
        c.line(50, y, width - 50, y)
        y -= 20

        # Line items
        c.setFont("Helvetica", 10)
        from sqlalchemy import inspect as sa_inspect
        inst = sa_inspect(invoice)
        invoice_lines = inst.dict.get('lines', []) or []
        
        for line in invoice_lines:
            unit_price = Decimal(str(line.unit_price))
            line_total = unit_price * line.qty
            c.drawString(50, y, str(line.product_id)[:30])
            c.drawString(300, y, str(line.qty))
            c.drawString(380, y, f"${unit_price:.2f}")
            c.drawString(480, y, f"${line_total:.2f}")
            y -= 20
            
            if y < 100:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)

        y -= 10
        c.line(50, y, width - 50, y)
        y -= 20

        # Totals
        c.drawString(380, y, "Subtotal:")
        c.drawString(480, y, f"${Decimal(str(invoice.subtotal)):.2f}")
        y -= 20

        if Decimal(str(invoice.discount_total)) > 0:
            c.drawString(380, y, "Discount:")
            c.drawString(480, y, f"-${Decimal(str(invoice.discount_total)):.2f}")
            y -= 20

        if Decimal(str(invoice.tax_total)) > 0:
            c.drawString(380, y, "Tax:")
            c.drawString(480, y, f"${Decimal(str(invoice.tax_total)):.2f}")
            y -= 20

        c.setFont("Helvetica-Bold", 11)
        c.drawString(380, y, "TOTAL:")
        c.drawString(480, y, f"${Decimal(str(invoice.total)):.2f}")
        y -= 20

        c.setFont("Helvetica", 10)
        c.drawString(380, y, "Amount Paid:")
        c.drawString(480, y, f"${Decimal(str(invoice.amount_paid)):.2f}")
        y -= 20

        amount_due = Decimal(str(invoice.total)) - Decimal(str(invoice.amount_paid))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(380, y, "Amount Due:")
        c.drawString(480, y, f"${amount_due:.2f}")
        y -= 40

        # Internal notes
        if mode == "internal":
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "INTERNAL NOTES (not visible to customer)")
            y -= 15
            c.setFont("Helvetica", 10)
            c.drawString(50, y, f"Discount ID: {invoice.discount_id or 'None'}")
            y -= 15
            c.drawString(50, y, f"Subscription: {invoice.subscription_id}")

        c.save()
        return buf.getvalue()
