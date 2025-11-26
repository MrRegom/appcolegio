from io import BytesIO
from typing import List
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from apps.reportes.dtos import ReportResult


def export_pdf(report: ReportResult, landscape_mode: bool = True) -> HttpResponse:
    """
    Genera un PDF simple con cabecera y tabla usando ReportLab.
    SRP: solo renderizado a PDF a partir de ReportResult.
    """
    buffer = BytesIO()
    page_size = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)

    styles = getSampleStyleSheet()
    elements: List = []

    elements.append(Paragraph(report.title, styles["Title"]))
    if report.filters_summary:
        filters_txt = " | ".join([f"{k}: {v}" for k, v in report.filters_summary.items() if v not in [None, ""]])
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(filters_txt, styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [report.columns] + report.rows
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#000000")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_value, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{report.title}.pdf"'
    return response


