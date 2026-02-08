from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black, blue, darkblue, red, green, grey


@dataclass(frozen=True)
class InvoicePDFData:
    invoice_id: str
    invoice_number: str
    company_legal_name: str
    company_id: str
    status: str
    subtotal_eur: Optional[Any] = None
    tax_eur: Optional[Any] = None
    total_eur: Optional[Any] = None
    issued_at: Optional[Any] = None
    due_at: Optional[Any] = None
    paid_at: Optional[Any] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceiptPDFData:
    invoice_id: str
    invoice_number: str
    company_legal_name: str
    company_id: str
    paid_at: Optional[Any] = None
    payment_reference: Optional[str] = None
    total_eur: Optional[Any] = None


def _format_currency(value: Any) -> str:
    """Format currency values."""
    if value is None:
        return "€0.00"
    try:
        # Handle various input types
        if isinstance(value, (int, float)):
            num = float(value)
        else:
            # Remove quotes and convert to float
            str_value = str(value).replace('"', '').replace("'", "").strip()
            num = float(str_value)
        return f"€{num:,.2f}"
    except (ValueError, TypeError):
        return f"€{value}"


def _format_date(date_value: Optional[Any]) -> str:
    """Format date values (can be string, datetime, or other)."""
    if not date_value:
        return "N/A"
    
    # If it's already a string
    if isinstance(date_value, str):
        try:
            # Clean the string
            date_str = date_value.replace('Z', '+00:00')
            # Try to parse as datetime
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d %B %Y")
        except (ValueError, AttributeError):
            # If parsing fails, return the string (truncated)
            return str(date_value)[:30]
    
    # If it's a datetime object
    elif hasattr(date_value, 'strftime'):
        try:
            return date_value.strftime("%d %B %Y")
        except:
            pass
    
    # For any other type
    try:
        return str(date_value)[:30]
    except:
        return "N/A"


def _draw_header(c, title: str):
    """Draw PDF header."""
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(darkblue)
    c.drawString(2*cm, 27*cm, title)
    
    # Draw line
    c.setStrokeColor(grey)
    c.setLineWidth(1)
    c.line(2*cm, 26.5*cm, 19*cm, 26.5*cm)
    
    c.setFillColor(black)


def render_invoice_pdf(data: InvoicePDFData) -> bytes:
    """Generate professional invoice PDF."""
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Draw header
    _draw_header(c, "INVOICE")
    
    # Invoice details section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, 25*cm, "Invoice Details")
    
    c.setFont("Helvetica", 10)
    y = 24*cm
    details = [
        ("Invoice Number:", str(data.invoice_number)),
        ("Invoice ID:", str(data.invoice_id)),
        ("Status:", str(data.status).upper()),
        ("Issued Date:", _format_date(data.issued_at)),
        ("Due Date:", _format_date(data.due_at)),
    ]
    
    for label, value in details:
        c.drawString(2*cm, y, label)
        c.drawString(6*cm, y, value)
        y -= 0.7*cm
    
    # Company details
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Billed To")
    y -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, str(data.company_legal_name))
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Company ID: {data.company_id}")
    
    # Financial summary
    y = 15*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Financial Summary")
    y -= 0.7*cm
    
    # Draw table
    c.setLineWidth(0.5)
    c.line(2*cm, y, 10*cm, y)
    y -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    rows = [
        ("Subtotal:", _format_currency(data.subtotal_eur)),
        ("Tax (0%):", _format_currency(data.tax_eur)),
    ]
    
    for label, value in rows:
        c.drawString(2*cm, y, label)
        c.drawString(8*cm, y, value)
        y -= 0.7*cm
    
    # Total line
    c.line(2*cm, y, 10*cm, y)
    y -= 0.7*cm
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(blue)
    c.drawString(2*cm, y, "TOTAL")
    c.drawString(8*cm, y, _format_currency(data.total_eur))
    c.setFillColor(black)
    
    # Payment status
    y -= 1.5*cm
    c.setFont("Helvetica-Bold", 12)
    status_str = str(data.status).lower()
    if status_str == "paid":
        c.setFillColor(green)
        c.drawString(2*cm, y, "✓ PAID")
    else:
        c.setFillColor(red)
        c.drawString(2*cm, y, "PENDING PAYMENT")
    c.setFillColor(black)
    
    if status_str == "paid":
        y -= 0.7*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, f"Paid on: {_format_date(data.paid_at)}")
        if data.payment_reference:
            y -= 0.7*cm
            c.drawString(2*cm, y, f"Reference: {data.payment_reference}")
    
    # Notes section
    if data.notes:
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Notes")
        y -= 0.5*cm
        
        c.setFont("Helvetica", 9)
        # Simple text wrapping
        notes_str = str(data.notes)
        words = notes_str.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) < 80:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines[:10]:  # Limit to 10 lines
            c.drawString(2*cm, y, line)
            y -= 0.5*cm
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(grey)
    c.drawString(2*cm, 2*cm, "Generated by Passenger Impact Engine")
    c.drawString(15*cm, 2*cm, "Page 1 of 1")
    
    c.save()
    return buffer.getvalue()


def render_receipt_pdf(data: ReceiptPDFData) -> bytes:
    """Generate professional payment receipt PDF."""
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Draw header with green color for receipt
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(green)
    c.drawString(2*cm, 27*cm, "PAYMENT RECEIPT")
    
    # Draw line
    c.setStrokeColor(grey)
    c.setLineWidth(1)
    c.line(2*cm, 26.5*cm, 19*cm, 26.5*cm)
    
    c.setFillColor(black)
    
    # Receipt details section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, 25*cm, "Payment Confirmation")
    
    c.setFont("Helvetica", 10)
    y = 24*cm
    details = [
        ("Invoice Number:", str(data.invoice_number)),
        ("Invoice ID:", str(data.invoice_id)),
        ("Payment Date:", _format_date(data.paid_at)),
    ]
    
    for label, value in details:
        c.drawString(2*cm, y, label)
        c.drawString(6*cm, y, value)
        y -= 0.7*cm
    
    # Company details
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Billed To")
    y -= 0.5*cm
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, str(data.company_legal_name))
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Company ID: {data.company_id}")
    
    # Payment confirmation box
    y = 15*cm
    c.setLineWidth(2)
    c.setStrokeColor(green)
    c.setFillColorRGB(0.9, 1.0, 0.9)
    c.roundRect(2*cm, y - 2*cm, 15*cm, 4*cm, 0.5*cm, stroke=1, fill=1)
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, "PAYMENT CONFIRMED")
    
    y -= 1*cm
    c.setFont("Helvetica", 12)
    if data.total_eur:
        amount = _format_currency(data.total_eur)
        c.drawCentredString(width/2, y, f"Amount Paid: {amount}")
    
    y -= 0.7*cm
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, y, "Thank you for your payment!")
    
    # Payment reference
    if data.payment_reference:
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, "Payment Reference:")
        y -= 0.5*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, str(data.payment_reference))
    
    # Important notes
    y -= 2*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Important Information:")
    y -= 0.5*cm
    
    notes = [
        "• This receipt confirms successful payment of the invoice",
        "• Please retain this document for your records",
        "• For any queries, contact support@passengerimpact.io",
        f"• Receipt generated on: {datetime.now().strftime('%d %B %Y %H:%M')}"
    ]
    
    c.setFont("Helvetica", 9)
    for note in notes:
        c.drawString(2.5*cm, y, note)
        y -= 0.5*cm
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(grey)
    c.drawString(2*cm, 2*cm, "Passenger Impact Engine — Automated Receipt")
    c.drawString(15*cm, 2*cm, "Official Document")
    
    c.save()
    return buffer.getvalue()
