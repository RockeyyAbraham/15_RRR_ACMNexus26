"""
DMCA Notice Generator for Sentinel.
programmatic PDF generation for legal takedown notices using ReportLab.
"""

from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# import other necessary reportlab modules

from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os

class DMCAGenerator:
    def __init__(self, output_dir="notices"):
        """Initialize the generator with an output directory."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_notice(self, detection_id, content_info, infringer_info):
        """
        Creates a legally compliant DMCA notice in PDF format.
        """
        filename = f"dmca_notice_{detection_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # 1. Header
        story.append(Paragraph("<b>DMCA TAKEDOWN NOTICE</b>", styles['Title']))
        story.append(Spacer(1, 0.2 * inch))

        # 2. Date and Recipient
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Paragraph("To: DMCA Abuse / Copyright Agent", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # 3. Protected Work Information
        story.append(Paragraph("<b>RE: Copyright Infringement of Protected Media</b>", styles['Heading2']))
        story.append(Paragraph(f"Protected Work: {content_info.get('title', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"Owner/League: {content_info.get('league', 'Unknown')}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # 4. Infringing Evidence
        story.append(Paragraph("<b>Description of Infringement:</b>", styles['Heading3']))
        story.append(Paragraph(f"Infringing URL: {infringer_info.get('url', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Detection Confidence: {infringer_info.get('confidence', 0):.2f}%", styles['Normal']))
        story.append(Paragraph(f"Detection Timestamp: {infringer_info.get('timestamp', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.4 * inch))

        # 5. Legal Affirmations
        legal_text = """
        I have a good faith belief that the use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law.
        <br/><br/>
        This notification is accurate, and under penalty of perjury, I am authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.
        """
        story.append(Paragraph("<b>Legal Affirmations:</b>", styles['Heading3']))
        story.append(Paragraph(legal_text, styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))

        # 6. Signature
        story.append(Paragraph("__________________________", styles['Normal']))
        story.append(Paragraph("Sentinel Automated Enforcement System", styles['Normal']))
        story.append(Paragraph("On behalf of the Copyright Holder", styles['Normal']))

        doc.build(story)
        return filepath

if __name__ == "__main__":
    # Test block for local validation
    gen = DMCAGenerator()
    content = {"title": "F1 Race Highlights", "league": "Formula 1"}
    infringer = {"url": "https://twitch.tv/pirate_stream", "confidence": 97.66, "timestamp": "2026-03-27 22:00:00"}
    path = gen.create_notice("TEST_001", content, infringer)
    print(f"✅ Generated test notice at: {path}")
