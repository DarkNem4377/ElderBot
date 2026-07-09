"""PDF field report generation (reportlab): summary, ranked zone table
with coordinates, and the full situation brief."""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas import AnalysisResult, Zone

MAX_ZONE_ROWS = 16


def _zone_coords(zone: Zone) -> str:
    if zone.centroid_lat is None or zone.centroid_lng is None:
        return "—"
    return f"{zone.centroid_lat:.4f}, {zone.centroid_lng:.4f}"


def _zone_row(zone: Zone) -> list[str]:
    return [
        str(zone.rank),
        _zone_coords(zone),
        str(zone.building_counts.destroyed),
        str(zone.building_counts.major),
        str(zone.building_counts.minor),
        str(zone.building_counts.none),
        f"{zone.priority_score:.1f}",
    ]


def generate_report_pdf(analysis: AnalysisResult, brief: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title="DisasterIQ Field Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], textColor=colors.HexColor("#0f172a")
    )
    heading_style = ParagraphStyle(
        "ReportHeading", parent=styles["Heading2"], textColor=colors.HexColor("#1e293b")
    )
    body_style = ParagraphStyle("ReportBody", parent=styles["BodyText"], leading=15)

    story = []
    story.append(Paragraph("DisasterIQ Field Damage Report", title_style))
    story.append(
        Paragraph(
            f"Pair: {escape(analysis.pair_id or 'Uploaded imagery')} &middot; "
            f"Inference mode: {escape(analysis.inference_mode)}",
            body_style,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Summary", heading_style))
    summary = analysis.summary
    story.append(
        Paragraph(
            f"Total buildings assessed: {summary.total_buildings}<br/>"
            f"Destroyed: {summary.destroyed_pct}%&nbsp;&nbsp;&nbsp;"
            f"Major: {summary.major_pct}%&nbsp;&nbsp;&nbsp;"
            f"Minor: {summary.minor_pct}%",
            body_style,
        )
    )
    if not analysis.geo_available:
        story.append(
            Paragraph(
                escape(analysis.geo_message or "Geographic coordinates unavailable for this imagery."),
                ParagraphStyle("GeoNote", parent=body_style, textColor=colors.HexColor("#92400e")),
            )
        )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Ranked Priority Zones", heading_style))
    table_data = [
        ["Rank", "Coordinates (lat, lng)", "Destroyed", "Major", "Minor", "None", "Priority"]
    ]
    table_data.extend(_zone_row(zone) for zone in analysis.zones[:MAX_ZONE_ROWS])

    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Situation Brief", heading_style))
    brief_lines = brief.splitlines() or [""]
    for line in brief_lines:
        story.append(Paragraph(escape(line) if line.strip() else "&nbsp;", body_style))

    doc.build(story)
    return buffer.getvalue()
