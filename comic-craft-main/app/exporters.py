from datetime import datetime
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = ROOT / "static" / "exports"


FONTS_DIR = ROOT / "static" / "fonts"


def save_pdf(layout: list[dict]) -> str:
    """Write one page per panel to static/exports; return the PDF's URL path."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_font("DejaVu", "", str(FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FONTS_DIR / "DejaVuSans-Bold.ttf"))
    pdf.add_font("DejaVu", "I", str(FONTS_DIR / "DejaVuSans-Oblique.ttf"))
    for panel in layout:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 16)
        pdf.multi_cell(0, 9, f"Panel {panel['panel']}: {panel['title']}", new_x="LMARGIN", new_y="NEXT")
        pdf.image(str(ROOT / panel["image"].lstrip("/")), x=30, w=150)
        pdf.ln(4)
        pdf.set_font("DejaVu", "I", 11)
        pdf.multi_cell(0, 6, panel["scene"], new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("DejaVu", "", 11)
        if panel["caption"]:
            pdf.multi_cell(0, 6, "Caption: " + panel["caption"], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        pdf.multi_cell(0, 6, panel["text"], new_x="LMARGIN", new_y="NEXT")
    name = f"comic_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    pdf.output(str(EXPORTS_DIR / name))
    return f"/static/exports/{name}"
