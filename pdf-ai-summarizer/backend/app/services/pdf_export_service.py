import markdown
import jinja2
import datetime
from pathlib import Path
from weasyprint import HTML

def create_summary_pdf(document_name: str, summary_text: str) -> bytes:
    summary_html = markdown.markdown(
        summary_text,
        extensions=["fenced_code", "tables"],
    )

    template_path = Path(__file__).parent.parent / "templates" / "summary_pdf.html"
    template_source = template_path.read_text(encoding="utf-8")
    
    rendered_html = jinja2.Template(template_source).render(
        document_name=document_name,
        generated_at= datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),      
        summary_html=summary_html,
    )
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    return pdf_bytes
