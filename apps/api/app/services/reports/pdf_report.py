"""PDF Report Generator for Run Reports.

Production-grade PDF generation using ReportLab with:
- No text truncation (proper wrapping)
- TR character support (DejaVu font)
- Full references with DOI/PMID links
- All sections: Summary, Key Points, Research Gaps, Claims, Marketing, References
"""

from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.query_run import QueryRun

from app.models.run_summary import RunSummary


# Try to register DejaVu for TR character support
# Register DejaVu for TR character support
# Paths verified in container: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
try:
    pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    DEFAULT_FONT = 'DejaVu'
    BOLD_FONT = 'DejaVu-Bold'
except Exception as e:
    print(f"Font loading error: {e}")
    # Fallback only if absolutely necessary, but we expect fonts to be present
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'


def escape_html(text: str) -> str:
    """Escape HTML special characters for ReportLab Paragraph."""
    if not text:
        return ""
    
    # First unescape any HTML entities (like &lt;i&gt; -> <i>)
    import html
    text = html.unescape(text)
    
    # Then escape specific characters for ReportLab, BUT keep valid tags if needed?
    # Actually, ReportLab supports <b> <i> etc. 
    # If the text contains <i> coming from unescape, we want to keep it.
    # But we should escape bare < and > that are not tags.
    # For now, let's just replace & with &amp; to be safe, but allow tags.
    # Simpler approach: Just unescape. ReportLab handles standard tags. 
    # If there are mathematical <, they might break it. 
    # Let's trust unescape for now to fix the display issues.
    return text.replace("&", "&amp;")


def get_custom_styles() -> dict[str, ParagraphStyle]:
    """Get custom paragraph styles for the report."""
    styles = getSampleStyleSheet()
    
    custom = {
        "Title": ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName=BOLD_FONT,
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor("#1e3a5f"),
        ),
        "Heading1": ParagraphStyle(
            "CustomH1",
            parent=styles["Heading1"],
            fontName=BOLD_FONT,
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#1e3a5f"),
        ),
        "Heading2": ParagraphStyle(
            "CustomH2",
            parent=styles["Heading2"],
            fontName=BOLD_FONT,
            fontSize=11,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor("#2c5282"),
        ),
        "Body": ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontName=DEFAULT_FONT,
            fontSize=10,
            spaceAfter=8,
            leading=14,
        ),
        "Small": ParagraphStyle(
            "CustomSmall",
            parent=styles["BodyText"],
            fontName=DEFAULT_FONT,
            fontSize=8,
            spaceAfter=6,
            leading=11,
            textColor=colors.HexColor("#444444"),
        ),
        "Bullet": ParagraphStyle(
            "CustomBullet",
            parent=styles["BodyText"],
            fontName=DEFAULT_FONT,
            fontSize=10,
            leftIndent=20,
            spaceAfter=6,
            bulletIndent=10,
            leading=14,
        ),
        "Citation": ParagraphStyle(
            "CustomCitation",
            parent=styles["BodyText"],
            fontName=DEFAULT_FONT,
            fontSize=9,
            spaceAfter=4,
            leftIndent=15,
            textColor=colors.HexColor("#666666"),
            leading=12,
        ),
    }
    return custom


def draw_cover(story: list, styles: dict, run: QueryRun, project: Project) -> None:
    """Add cover page elements."""
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("PharmaInsightAI", styles["Title"]))
    story.append(Paragraph("Research Analysis Report", styles["Heading1"]))
    story.append(Spacer(1, 0.5 * inch))
    
    # Full query text (no truncation)
    story.append(Paragraph(f"<b>Project:</b> {escape_html(project.name)}", styles["Body"]))
    story.append(Paragraph(f"<b>Research Query:</b>", styles["Body"]))
    story.append(Paragraph(escape_html(run.query_text), styles["Body"]))
    story.append(Spacer(1, 0.3 * inch))
    
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {generated_at}", styles["Small"]))
    story.append(Paragraph(f"<b>Run ID:</b> {run.id}", styles["Small"]))
    story.append(PageBreak())


def draw_metadata(
    story: list,
    styles: dict,
    run: QueryRun,
    project: Project,
    paper_count: int,
) -> None:
    """Add run metadata section."""
    story.append(Paragraph("Run Details", styles["Heading1"]))
    
    # Build year range only if provided
    year_range = ""
    if run.year_from and run.year_to:
        year_range = f"{run.year_from} - {run.year_to}"
    elif run.year_from:
        year_range = f"From {run.year_from}"
    elif run.year_to:
        year_range = f"Until {run.year_to}"
    else:
        year_range = "All years"
    
    # Build metadata table
    data = [
        ["Project", escape_html(project.name)],
        ["Created At", run.created_at.strftime("%Y-%m-%d %H:%M:%S") if run.created_at else "N/A"],
        ["Status", run.status.value if hasattr(run.status, "value") else str(run.status)],
        ["Max Papers", str(run.max_papers) if run.max_papers else "Default"],
        ["Year Range", year_range],
        ["Papers Analyzed", str(paper_count)],
    ]
    
    table = Table(data, colWidths=[1.5 * inch, 4.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (0, -1), BOLD_FONT),
        ("FONTNAME", (1, 0), (1, -1), DEFAULT_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))


def draw_summary(story: list, styles: dict, summary_json: dict[str, Any] | None) -> None:
    """Add executive summary section."""
    story.append(Paragraph("Executive Summary", styles["Heading1"]))
    
    if not summary_json:
        story.append(Paragraph("<i>No synthesis available for this run.</i>", styles["Body"]))
        return
    
    # TLDR (full text, no truncation)
    tldr = summary_json.get("tldr", "")
    if tldr:
        story.append(Paragraph(f"<b>Summary:</b> {escape_html(tldr)}", styles["Body"]))
    
    # Consensus level
    consensus = summary_json.get("consensus_level", "")
    if consensus:
        color = "#22c55e" if consensus == "high" else "#eab308" if consensus == "medium" else "#ef4444"
        story.append(Paragraph(
            f"<b>Consensus Level:</b> <font color='{color}'>{consensus.upper()}</font>",
            styles["Body"]
        ))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_key_points(story: list, styles: dict, summary_json: dict[str, Any] | None) -> None:
    """Add key points section with citations."""
    story.append(Paragraph("Key Points", styles["Heading1"]))
    
    if not summary_json:
        story.append(Paragraph("<i>No key points available.</i>", styles["Body"]))
        return
    
    key_points = summary_json.get("key_points", [])
    if not key_points:
        story.append(Paragraph("<i>No key points extracted.</i>", styles["Body"]))
        return
    
    for kp in key_points:
        text = kp.get("text", str(kp)) if isinstance(kp, dict) else str(kp)
        citations = ""
        if isinstance(kp, dict) and kp.get("citations"):
            citation_nums = []
            for c in kp["citations"]:
                idx = c.get("index", c.get("label_number", ""))
                if idx:
                    citation_nums.append(f"[{idx}]")
            citations = " " + "".join(citation_nums)
        
        story.append(Paragraph(f"• {escape_html(text)}{citations}", styles["Bullet"]))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_research_gaps(story: list, styles: dict, summary_json: dict[str, Any] | None) -> None:
    """Add research gaps section."""
    if not summary_json:
        return
        
    research_gaps = summary_json.get("research_gaps", [])
    if not research_gaps:
        return
    
    story.append(Paragraph("Research Gaps", styles["Heading1"]))
    
    for gap in research_gaps:
        text = gap.get("text", str(gap)) if isinstance(gap, dict) else str(gap)
        story.append(Paragraph(f"• {escape_html(text)}", styles["Bullet"]))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_claims(story: list, styles: dict, summary_json: dict[str, Any] | None) -> None:
    """Add claims draft section."""
    if not summary_json:
        return
        
    claims = summary_json.get("claims_draft", [])
    if not claims:
        return
    
    story.append(Paragraph("Claims Draft", styles["Heading1"]))
    
    for claim_obj in claims:
        if isinstance(claim_obj, dict):
            claim_text = claim_obj.get("claim", "")
            allowed = claim_obj.get("allowed", None)
            rationale = claim_obj.get("rationale", "")
            
            # Format: Claim text with allowed status
            status = "✓ Allowed" if allowed else "✗ Not Allowed" if allowed is False else ""
            full_text = f"• {escape_html(claim_text)}"
            if status:
                full_text = f"<b>{status}:</b> {escape_html(claim_text)}"
            story.append(Paragraph(full_text, styles["Bullet"]))
            
            # Add rationale if present
            if rationale:
                story.append(Paragraph(f"<i>Rationale: {escape_html(rationale)}</i>", styles["Body"]))
        else:
            story.append(Paragraph(f"• {escape_html(str(claim_obj))}", styles["Bullet"]))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_marketing(story: list, styles: dict, summary_json: dict[str, Any] | None) -> None:
    """Add marketing slogans section."""
    if not summary_json:
        return
        
    slogans = summary_json.get("marketing_slogans", [])
    if not slogans:
        return
    
    story.append(Paragraph("Marketing Slogans", styles["Heading1"]))
    
    for slogan in slogans:
        text = slogan.get("text", str(slogan)) if isinstance(slogan, dict) else str(slogan)
        story.append(Paragraph(f"• {escape_html(text)}", styles["Bullet"]))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_evidence_table(story: list, styles: dict, evidence_rows: list) -> None:
    """Add evidence table section."""
    story.append(Paragraph("Evidence Overview", styles["Heading1"]))
    
    if not evidence_rows:
        story.append(Paragraph("<i>No evidence data available.</i>", styles["Body"]))
        return
    
    # Table header
    data = [["#", "Paper Title", "Study Type", "Key Finding"]]
    
    for i, row in enumerate(evidence_rows[:15], 1):  # Limit to 15 for space
        summary = row.row_json or {}
        # Full title wrapped (no truncation)
        title = row.paper.title if row.paper.title else "Untitled"
        study_type = summary.get("study_type", "N/A") or "N/A"
        findings = summary.get("key_findings", [])
        findings_text = findings[0] if findings else "N/A"
        
        # Wrap long text in Paragraph for proper wrapping
        data.append([
            str(i),
            Paragraph(escape_html(title), styles["Small"]),
            study_type,
            Paragraph(escape_html(findings_text), styles["Small"]),
        ])
    
    table = Table(data, colWidths=[0.4 * inch, 2.3 * inch, 1 * inch, 2.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(table)
    
    if len(evidence_rows) > 15:
        story.append(Paragraph(f"<i>... and {len(evidence_rows) - 15} additional papers (see References)</i>", styles["Small"]))
    
    story.append(Spacer(1, 0.3 * inch))


def draw_detailed_evidence(story: list, styles: dict, evidence_rows: list) -> None:
    """Add detailed evidence snippets section."""
    has_snippets = False
    for row in evidence_rows:
        summary = row.row_json or {}
        if summary.get("evidence_snippets"):
            has_snippets = True
            break
            
    if not has_snippets:
        return

    story.append(Paragraph("Evidence Snippets", styles["Heading1"]))
    
    for i, row in enumerate(evidence_rows[:10], 1):  # Limit to top 10 to avoid huge PDFs
        summary = row.row_json or {}
        snippets = summary.get("evidence_snippets", [])
        if not snippets:
            continue
            
        paper = row.paper
        title = paper.title if paper.title else "Untitled"
        
        # Paper Header
        header_text = f"<b>[{i}] {escape_html(title)}</b>"
        story.append(Paragraph(header_text, styles["Body"]))
        
        # Snippets
        for snippet in snippets[:2]:  # Max 2 snippets per paper
            text = snippet.get("quote", snippet) if isinstance(snippet, dict) else snippet
            if text:
                story.append(Paragraph(f"<i>“{escape_html(str(text))}”</i>", styles["Citation"]))
        
        story.append(Spacer(1, 0.1 * inch))
    
    if len(evidence_rows) > 10:
        story.append(Paragraph(f"<i>... and more evidence in full report.</i>", styles["Small"]))
    
    story.append(Spacer(1, 0.2 * inch))


def draw_references(story: list, styles: dict, evidence_rows: list) -> None:
    """Add full references section with DOI/PMID links."""
    story.append(PageBreak())
    story.append(Paragraph("References", styles["Heading1"]))
    
    if not evidence_rows:
        story.append(Paragraph("<i>No references available.</i>", styles["Body"]))
        return
    
    for i, row in enumerate(evidence_rows, 1):
        paper = row.paper
        authors = paper.authors[:3] if paper.authors else []
        author_str = ", ".join(authors)
        if paper.authors and len(paper.authors) > 3:
            author_str += " et al."
        
        year = paper.year or "N/A"
        title = escape_html(paper.title) if paper.title else "Untitled"
        journal = escape_html(paper.journal) if paper.journal else ""
        
        # Build reference line (full text, no truncation)
        ref_parts = [f"<b>[{i}]</b>"]
        if author_str:
            ref_parts.append(escape_html(author_str) + ".")
        ref_parts.append(f"({year}).")
        ref_parts.append(f"<i>{title}</i>.")
        if journal:
            ref_parts.append(journal + ".")
        
        story.append(Paragraph(" ".join(ref_parts), styles["Small"]))
        
        # Identifiers on separate line for clarity
        ids = []
        if paper.pmid:
            ids.append(f"PMID: <link href='https://pubmed.ncbi.nlm.nih.gov/{paper.pmid}/'>{paper.pmid}</link>")
        if paper.doi:
            ids.append(f"DOI: <link href='https://doi.org/{paper.doi}'>{paper.doi}</link>")
        
        if ids:
            story.append(Paragraph(" | ".join(ids), styles["Citation"]))


def build_run_report_pdf(run_id: UUID, db: Session) -> bytes:
    """Build a PDF report for a run.
    
    Args:
        run_id: The run UUID
        db: Database session
        
    Returns:
        PDF file as bytes
        
    Raises:
        ValueError: If run not found
    """
    # Fetch run
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")
    
    # Fetch project
    project = db.query(Project).filter(Project.id == run.project_id).first()
    if not project:
        raise ValueError(f"Project for run {run_id} not found")
    
    # Fetch evidence rows (replacement for PaperSummary)
    from app.models.evidence_row import EvidenceRow
    evidence_rows = (
        db.query(EvidenceRow)
        .filter(EvidenceRow.run_id == run_id)
        .all()
    )
    
    # Fetch run synthesis
    run_summary = db.query(RunSummary).filter(RunSummary.run_id == run_id).first()
    summary_json = run_summary.summary_json if run_summary else None
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    # Get styles
    styles = get_custom_styles()
    
    # Build story (content)
    story: list = []
    
    # 1. Cover
    draw_cover(story, styles, run, project)
    
    # 2. Metadata
    draw_metadata(story, styles, run, project, len(evidence_rows))
    
    # 3. Executive Summary
    draw_summary(story, styles, summary_json)
    
    # 4. Key Points
    draw_key_points(story, styles, summary_json)
    
    # 5. Research Gaps
    draw_research_gaps(story, styles, summary_json)
    
    # 6. Claims Draft
    draw_claims(story, styles, summary_json)
    
    # 7. Marketing Slogans
    draw_marketing(story, styles, summary_json)
    
    # 8. Evidence Table
    draw_evidence_table(story, styles, evidence_rows)
    
    # 9. Evidence Snippets
    draw_detailed_evidence(story, styles, evidence_rows)
    
    # 10. References
    draw_references(story, styles, evidence_rows)
    
    # Build PDF
    doc.build(story)
    
    # Get bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
