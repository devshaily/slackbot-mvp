import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# Output directory (will be created if not exists)
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_pdf(batch_id: str, cleaned: list[str], groups: list[dict], outlines: dict, post_ideas: dict) -> str:
    # batch_id doubles as slug for MVP
    slug = batch_id
    pdf_path = os.path.join(OUTPUT_DIR, f"report_{slug}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    def line(text: str, y: float, bold: bool = False) -> float:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10 if not bold else 12)
        c.drawString(margin, y, text)
        return y - 14

    y = height - margin
    c.setTitle(f"Keyword Report – {slug}")

    y = line("Keyword Content Report", y, bold=True)
    y = line(f"Batch: {slug}", y)

    # Keywords
    y -= 6
    y = line("Cleaned Keywords:", y, bold=True)
    for kw in cleaned:
        if y < 2 * cm:
            c.showPage()
            y = height - margin
        y = line(f"• {kw}", y)

    # Groups
    y -= 6
    y = line("\nGroups:", y, bold=True)
    for g in groups:
        if y < 2 * cm:
            c.showPage()
            y = height - margin
        y = line(f"▶ {g['label']} ({len(g['items'])})", y, bold=True)
        for it in g['items'][:20]:
            if y < 2 * cm:
                c.showPage()
                y = height - margin
            y = line(f"   - {it}", y)

        # Outline
        outline = outlines.get(g["label"])
        if outline:
            if y < 2 * cm:
                c.showPage()
                y = height - margin
            y = line(f"   Outline: {outline.get('title', '')}", y)
            for sec in outline.get("sections", [])[:8]:
                if y < 2 * cm:
                    c.showPage()
                    y = height - margin
                y = line(f"     • {sec['heading']}", y)

    # -------------------------------
    # Suggested Post Ideas Section
    # -------------------------------
    y -= 10
    if y < 2 * cm:
        c.showPage()
        y = height - margin
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Suggested Post Ideas")
    y -= 15
    c.setFont("Helvetica", 10)
    
    for g in groups:
        ideas = post_ideas.get(g['label'], [])
        if not ideas:
            continue
    
        if y < 2 * cm:
            c.showPage()
            y = height - margin
    
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, f"{g['label']}:")
        y -= 12
        c.setFont("Helvetica", 10)
    
        for idea in ideas:
            if y < 2 * cm:
                c.showPage()
                y = height - margin
            c.drawString(margin + 20, y, f"• {idea}")
            y -= 12

    c.save()
    return pdf_path
