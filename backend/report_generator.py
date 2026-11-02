from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_report(item):
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=42)
    s=getSampleStyleSheet()
    story=[Paragraph("AI-Powered Fake News Detection Report",s["Title"]),Spacer(1,14)]
    for label,key in [("Analysis ID","id"),("Date","created_at"),("Headline","title"),("Prediction","prediction"),
                      ("Model confidence","confidence"),("Language","language"),("Explanation","explanation")]:
        story.append(Paragraph(f"<b>{label}:</b> {escape(str(item.get(key) if item.get(key) is not None else 'Not available'))}",s["BodyText"]))
        story.append(Spacer(1,7))
    story += [Spacer(1,8),Paragraph("<b>Submitted text</b>",s["Heading2"]),
              Paragraph(escape(str(item.get("article_text",""))[:12000]).replace("\n","<br/>"),s["BodyText"]),
              Spacer(1,12),Paragraph("<b>Important limitation</b>",s["Heading2"]),
              Paragraph("This is an automated model prediction, not independent fact verification. Confidence is not the probability that the article is true. Verify important claims using reliable independent sources.",s["BodyText"])]
    doc.build(story); buf.seek(0); return buf
