"""
DMCA Notice Generator for Sentinel.
Programmatic PDF generation for legal takedown notices using ReportLab.
"""

import os
import traceback
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.pdfgen import canvas

class PageNumCanvas(canvas.Canvas):
    """
    Custom canvas for ReportLab to handle page numbering (Page X of Y).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        # Position: Right-aligned, bottom footer
        self.drawRightString(7.5 * inch, 0.5 * inch, f"Page {self._pageNumber} of {page_count}")

class DMCAGenerator:
    def __init__(self, output_dir="notices"):
        """Initialize the generator with an output directory."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_notice_path(self, detection_id):
        """Returns the expected output path for a given detection ID."""
        filename = f"dmca_notice_{detection_id}.pdf"
        return os.path.join(self.output_dir, filename)

    def attach_evidence_frame(self, frame_source, styles):
        """
        Helper to resize evidence frame for PDF embedding.
        Accepts a PIL Image or file path.
        """
        try:
            img = RLImage(frame_source)
            max_w, max_h = 400, 225
            
            # Use imageWidth and imageHeight from RLImage
            img_w, img_h = img.imageWidth, img.imageHeight
            aspect = img_w / img_h
            
            if aspect > (max_w / max_h):
                img.drawWidth = max_w
                img.drawHeight = max_w / aspect
            else:
                img.drawHeight = max_h
                img.drawWidth = max_h * aspect
            return img
        except Exception:
            return Paragraph("<i>Evidence frame not available</i>", styles['Normal'])

    def generate_with_ai(self, detection_id, content_info, infringer_info, rights_holder, ai_text=None, evidence_frame=None):
        """
        Primary entrypoint for generating high-fidelity DMCA notices.
        Supports both AI-generated and template-based text.
        """
        filepath = self.get_notice_path(detection_id)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Custom styles
            warning_style = ParagraphStyle(
                'Warning',
                parent=styles['Normal'],
                textColor=colors.HexColor("#FF0000"),
                fontSize=10,
                alignment=1, # Center
                borderPadding=5,
                backColor=colors.HexColor("#FFF0F0")
            )
            
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                spaceBefore=12,
                spaceAfter=6,
                borderWidth=0,
                fontSize=14
            )

            story = []

            # 1. Warning Banner
            story.append(Paragraph("<b>⚠ DMCA NOTICE GENERATED FOR REVIEW — NOT AUTO-SENT.</b>", warning_style))
            story.append(Paragraph("Legal team must review before submission.", warning_style))
            story.append(Spacer(1, 0.3 * inch))

            # 2. Main Title
            story.append(Paragraph("<b>DMCA TAKEDOWN NOTICE</b>", styles['Title']))
            story.append(Spacer(1, 0.2 * inch))

            # 3. Date and Rights Holder Section
            story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
            
            if rights_holder:
                story.append(Paragraph("<b>Rights Holder Information:</b>", section_style))
                story.append(Paragraph(f"<b>Name:</b> {rights_holder.get('name', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Email:</b> {rights_holder.get('email', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Address:</b> {rights_holder.get('address', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"<b>Phone:</b> {rights_holder.get('phone', 'N/A')}", styles['Normal']))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceBefore=4, spaceAfter=10))

            # 4. Protected Work Section
            story.append(Paragraph("<b>Protected Content Details:</b>", section_style))
            story.append(Paragraph(f"<b>Content Title:</b> {content_info.get('title', 'Unknown')}", styles['Normal']))
            story.append(Paragraph(f"<b>Owner/League:</b> {content_info.get('league', 'Unknown')}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

            # 5. Evidence Section
            story.append(Paragraph("<b>Identification of Infringing Material (Evidence):</b>", section_style))
            story.append(Paragraph(f"<b>Detection ID:</b> {detection_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Infringing URL:</b> {infringer_info.get('url', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Confidence:</b> {infringer_info.get('confidence', 0):.2f}%", styles['Normal']))
            story.append(Paragraph(f"<b>Detected At:</b> {infringer_info.get('timestamp', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Matching Method:</b> Multi-modal pHash + mel-spectrogram audio fingerprinting with Hamming distance comparison", styles['Normal']))
            
            # Perceptual Hash Reference
            hash_ref = infringer_info.get('hash_ref', 'N/A')
            if hash_ref and hash_ref != 'N/A':
                story.append(Paragraph(f"<b>Perceptual Fingerprint Fragment:</b> {hash_ref[:16]}...", styles['Normal']))
            
            story.append(Spacer(1, 0.15 * inch))
            
            # Evidence Frame
            if evidence_frame:
                img = self.attach_evidence_frame(evidence_frame, styles)
                story.append(img)
            else:
                # Placeholder box
                story.append(Paragraph("Evidence frame not available", styles['Italic']))

            story.append(Spacer(1, 0.3 * inch))

            # 6. Legal Text Segment
            story.append(Paragraph("<b>Legal Declaration:</b>", section_style))
            if ai_text:
                story.append(Paragraph(ai_text, styles['Normal']))
            else:
                # Default template text
                default_legal = """
                I have a good-faith belief that the use of the copyrighted materials described above is not authorized by the copyright owner, its agent, or the law.<br/><br/>
                I swear, under penalty of perjury, that the information in this notification is accurate and that I am the copyright owner or am authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.
                """
                story.append(Paragraph(default_legal, styles['Normal']))
            
            story.append(Spacer(1, 0.5 * inch))

            # 7. Signature Block
            story.append(Paragraph("<b>Digital Signature & Authority:</b>", section_style))
            story.append(Paragraph("__________________________", styles['Normal']))
            story.append(Paragraph(f"<b>Printed Name:</b> [LEGAL_REPRESENTATIVE_NAME]", styles['Normal']))
            story.append(Paragraph(f"<b>Title/Office:</b> [DEPT_LEGAL_COMPLIANCE]", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("<i>Note: This notice was generated by the Sentinel Automated Enforcement System pending final human review.</i>", styles['Normal']))

            # Build PDF with PageNumCanvas for page numbering
            doc.build(story, canvasmaker=PageNumCanvas)
            return filepath

        except Exception as e:
            # Fallback PDF on failure
            try:
                error_msg = str(e)
                stack_trace = traceback.format_exc()
                c = canvas.Canvas(filepath, pagesize=letter)
                c.drawString(1 * inch, 10.5 * inch, f"ERROR: DMCA Notice Generation Failed for ID: {detection_id}")
                c.drawString(1 * inch, 10 * inch, f"Timestamp: {datetime.now().isoformat()}")
                c.setFont("Helvetica", 8)
                c.drawString(1 * inch, 9.5 * inch, f"Exception: {error_msg}")
                # Save first page
                c.save()
                return filepath
            except:
                return f"ERROR: Could not generate even fallback PDF: {str(e)}"

    def create_notice(self, detection_id, content_info, infringer_info):
        """
        Original entrypoint for backward compatibility.
        Wrapper around generate_with_ai with default parameters.
        """
        # We attempt to find matching rights holder or use defaults
        rights_holder = {
            "name": "Sentinel Rights Management Team",
            "email": "legal@sentinel-defense.ai",
            "address": "San Francisco, CA, USA",
            "phone": "+1 (000) 000-0000"
        }
        return self.generate_with_ai(detection_id, content_info, infringer_info, rights_holder=rights_holder)

if __name__ == "__main__":
    # Test block for local validation
    gen = DMCAGenerator()
    content = {"title": "Premier League: Match Day 12", "league": "Premier League"}
    infringer = {
        "url": "https://twitch.tv/pirate_match_12", 
        "confidence": 98.45, 
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "hash_ref": "a2f9b2c3d4e5f607"
    }
    rights = {
        "name": "Acme Media Corp",
        "email": "takedowns@acmemedia.com",
        "address": "123 Broadcast Hill, NY 10001",
        "phone": "+1 212 555 0199"
    }
    
    # Test typical AI generation
    path = gen.generate_with_ai("PROD_001", content, infringer, rights, ai_text="This is an AI-generated legal statement produced by Sentinel AI.")
    print(f"SUCCESS: Generated AI-powered notice at: {path}")
    
    # Test backward compatibility
    path_basic = gen.create_notice("COMPAT_002", content, infringer)
    print(f"SUCCESS: Generated compatibility notice at: {path_basic}")
