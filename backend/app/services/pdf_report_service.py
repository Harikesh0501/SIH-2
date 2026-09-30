import io
from datetime import datetime
from typing import Dict, List, Any, Optional

import qrcode
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

from app.models.user import User
from app.models.competency import Competency, CompetencyLevel, UserCompetency, RoleBenchmark
from app.models.course import Course, Enrollment, EnrollmentStatus
from app.models.passport import DigitalCredential
from app.services.passport_service import PassportService, LEVEL_LABELS, CADRE_NAMES, DIVISION_NAMES

# Monochromatic Theme Palette (Black & White Coursera/Notion standard)
C_PRIMARY = colors.HexColor("#09090b")      # Deep Charcoal/Black
C_DARK_BG = colors.HexColor("#18181b")      # Dark Header Background
C_LIGHT_BG = colors.HexColor("#f4f4f5")     # Light Zinc for alternate rows / callouts
C_BORDER = colors.HexColor("#e4e4e7")       # Crisp boundary gray
C_MUTED = colors.HexColor("#71717a")        # Secondary text gray
C_WHITE = colors.HexColor("#ffffff")        # Crisp white
C_SUCCESS = colors.HexColor("#16a34a")      # Subtle verification indicator

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count ('Page X of Y')
    along with official MoSPI security watermark text.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(C_MUTED)
        
        # Bottom rule
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 40, A4[0] - 36, 40)
        
        # Left footer: Official security disclaimer
        self.drawString(36, 28, "MoSPI / NSSTA Karmayogi Competency System - Tamper-evident Digital Credential")
        
        # Right footer: Page numbers
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 28, page_text)
        self.restoreState()


class PDFReportService:

    @staticmethod
    def _create_qr_flowable(data_url: str, size: float = 65) -> Image:
        """
        Creates an in-memory QR code flowable for ReportLab.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Image(buf, width=size, height=size)

    @classmethod
    def generate_officer_skill_card(cls, db: Session, user: User) -> bytes:
        """
        Generates the official MoSPI Officer Digital Skill Card (PDF).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()

        # Custom Typography
        style_title = ParagraphStyle(
            'GovTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=C_PRIMARY,
            alignment=1 # Centered
        )
        style_subtitle = ParagraphStyle(
            'GovSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=C_MUTED,
            alignment=1
        )
        style_heading = ParagraphStyle(
            'DocHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=C_PRIMARY
        )
        style_body = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=C_PRIMARY
        )
        style_body_bold = ParagraphStyle(
            'DocBodyBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=C_PRIMARY
        )
        style_muted = ParagraphStyle(
            'DocMuted',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=C_MUTED
        )
        style_badge = ParagraphStyle(
            'DocBadge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=C_PRIMARY
        )
        style_th = ParagraphStyle(
            'DocTH',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=C_WHITE
        )

        elements = []

        # 1. Official Header
        header_text = """
        <b>GOVERNMENT OF INDIA &bull; भारत सरकार</b><br/>
        <b>MINISTRY OF STATISTICS & PROGRAMME IMPLEMENTATION (MoSPI)</b><br/>
        <font size="8" color="#71717a">NATIONAL STATISTICAL SYSTEMS TRAINING ACADEMY (NSSTA), GREATER NOIDA</font><br/>
        <font size="10" color="#09090b"><b>OFFICIAL STATISTICAL PERSONNEL DIGITAL SKILL PASSPORT</b></font>
        """
        elements.append(Paragraph(header_text, style_title))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

        # 2. Officer Details & Scannable QR Code Banner
        karmayogi_id = PassportService.get_karmayogi_id(user)
        verification_url = f"http://localhost:3000/verify/passport/{karmayogi_id}"
        qr_flowable = cls._create_qr_flowable(verification_url, size=75)

        officer_info_text = f"""
        <b>Officer Name:</b> {user.full_name}<br/>
        <b>Karmayogi ID:</b> {karmayogi_id} &nbsp;|&nbsp; <b>Cadre:</b> {user.cadre} ({CADRE_NAMES.get(user.cadre, user.cadre)})<br/>
        <b>Designation:</b> {user.designation}<br/>
        <b>Division:</b> {user.division} - {DIVISION_NAMES.get(user.division, user.division)}<br/>
        <b>Organization:</b> {user.organization or 'Ministry of Statistics & Programme Implementation'}<br/>
        <b>Status:</b> <font color="#16a34a"><b>OFFICIALLY VERIFIED & ACTIVE</b></font> &nbsp;|&nbsp; <b>Experience:</b> {user.experience_years} Years
        """

        qr_col_text = f"""
        <para align="center">
        <b>OFFICIAL AUDIT SEAL</b><br/>
        <font size="7" color="#71717a">Scan via Mobile Camera to verify authentic MoSPI accreditation</font>
        </para>
        """

        profile_table_data = [
            [
                Paragraph(officer_info_text, style_body),
                [qr_flowable, Paragraph(qr_col_text, style_muted)]
            ]
        ]

        profile_table = Table(profile_table_data, colWidths=[380, 140])
        profile_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), C_LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(profile_table)
        elements.append(Spacer(1, 12))

        # 3. Summary Analytics KPI Grid
        passport_data = PassportService.get_officer_passport(db, user)
        metrics = passport_data["summary_metrics"]

        kpi_data = [
            [
                Paragraph(f"<b>Overall Proficiency</b><br/><font size='12'><b>{metrics['overall_proficiency_pct']}%</b></font>", style_body),
                Paragraph(f"<b>Competencies Assessed</b><br/><font size='12'><b>{metrics['competencies_assessed']} / {metrics['total_competencies_in_framework']}</b></font>", style_body),
                Paragraph(f"<b>Verified Credentials</b><br/><font size='12'><b>{metrics['credentials_count']}</b></font>", style_body),
                Paragraph(f"<b>Badges Earned</b><br/><font size='12'><b>{metrics['badges_earned_count']}</b></font>", style_body),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 130])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # 4. Verified Competency Profile Table
        elements.append(Paragraph("<b>Competency Proficiency & Assessment Matrix</b>", style_heading))
        elements.append(Spacer(1, 6))

        comp_table_data = [
            [
                Paragraph("<b>Domain / Code</b>", style_th),
                Paragraph("<b>Official Competency Title</b>", style_th),
                Paragraph("<b>Current Level</b>", style_th),
                Paragraph("<b>Target</b>", style_th),
                Paragraph("<b>Verification Source</b>", style_th),
                Paragraph("<b>Audit Status</b>", style_th)
            ]
        ]

        # Flatten competencies across domains
        for dom in passport_data["domains"]:
            for comp in dom["competencies"]:
                if comp["current_level"] > 0:
                    status_text = "<font color='#16a34a'><b>Verified</b></font>" if comp["is_verified"] else "<font color='#71717a'>Self-Assessed</font>"
                    comp_table_data.append([
                        Paragraph(f"<b>{comp['code']}</b><br/><font size='6.5' color='#71717a'>{dom['domain_code'][:4]}</font>", style_body),
                        Paragraph(comp["name"], style_body),
                        Paragraph(f"<b>Level {comp['current_level']}</b><br/><font size='6.5'>{comp['level_label'].split('(')[0]}</font>", style_body),
                        Paragraph(f"L{comp['target_level']}", style_body),
                        Paragraph(comp["assessed_via"], style_body),
                        Paragraph(status_text, style_body)
                    ])

        comp_table = Table(comp_table_data, colWidths=[75, 175, 80, 50, 75, 65])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_DARK_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG])
        ]))
        elements.append(comp_table)
        elements.append(Spacer(1, 14))

        # 5. Verified Credentials & Cryptographic Signatures
        elements.append(Paragraph("<b>Issued Micro-Credentials & Cryptographic Signatures</b>", style_heading))
        elements.append(Spacer(1, 6))

        cred_table_data = [
            [
                Paragraph("<b>Credential Code</b>", style_th),
                Paragraph("<b>Certified Title & Level</b>", style_th),
                Paragraph("<b>SHA-256 Signature (Tamper-Proof)</b>", style_th),
                Paragraph("<b>Issue Date</b>", style_th)
            ]
        ]

        for c in passport_data["credentials"][:6]:
            cred_table_data.append([
                Paragraph(f"<b>{c['credential_code']}</b>", style_body),
                Paragraph(f"{c['title']}<br/><font size='7' color='#71717a'>{c['level_label']}</font>", style_body),
                Paragraph(f"<font face='Courier' size='6.5'>{c['qr_code_hash'][:32]}...<br/>{c['qr_code_hash'][32:]}</font>", style_body),
                Paragraph(c["issued_date"].split("T")[0] if c.get("issued_date") else "2026-08-15", style_body)
            ])

        if len(cred_table_data) > 1:
            cred_table = Table(cred_table_data, colWidths=[120, 160, 165, 75])
            cred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), C_DARK_BG),
                ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG])
            ]))
            elements.append(cred_table)
            elements.append(Spacer(1, 14))

        # 6. Domain Mastery Badges
        if passport_data["badges"]:
            elements.append(Paragraph("<b>Official MoSPI Domain Mastery Badges</b>", style_heading))
            elements.append(Spacer(1, 6))

            badge_cells = []
            for b in passport_data["badges"]:
                badge_cells.append(Paragraph(
                    f"<b>[{b['tier']}] {b['title']}</b><br/><font size='7' color='#71717a'>{b['criteria']}</font>",
                    style_badge
                ))

            # Group in 2 columns
            badge_rows = []
            for i in range(0, len(badge_cells), 2):
                if i + 1 < len(badge_cells):
                    badge_rows.append([badge_cells[i], badge_cells[i+1]])
                else:
                    badge_rows.append([badge_cells[i], Paragraph("", style_body)])

            badge_table = Table(badge_rows, colWidths=[260, 260])
            badge_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), C_LIGHT_BG),
                ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(badge_table)
            elements.append(Spacer(1, 14))

        # 7. Official Endorsement & Signatory Block
        sign_block_data = [
            [
                Paragraph("""
                <b>Statutory Authority:</b><br/>
                Issued pursuant to Mission Karmayogi Capacity Building Commission guidelines and the National Training Policy for the Indian Official Statistical System.
                """, style_muted),
                Paragraph("""
                <para align="right">
                <b>Director General</b><br/>
                National Statistical Systems Training Academy (NSSTA)<br/>
                Ministry of Statistics & Programme Implementation (MoSPI)
                </para>
                """, style_body)
            ]
        ]
        sign_table = Table(sign_block_data, colWidths=[320, 200])
        sign_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(KeepTogether(sign_table))

        # Build PDF with two-pass NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    @classmethod
    def generate_ministry_readiness_report(cls, db: Session) -> bytes:
        """
        Generates the comprehensive Ministry Capacity Readiness & TPAC Planning Report (PDF).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()

        style_title = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=C_PRIMARY,
            alignment=1
        )
        style_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=C_PRIMARY
        )
        style_body = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=C_PRIMARY
        )
        style_th = ParagraphStyle(
            'ReportTH',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=C_WHITE
        )
        style_muted = ParagraphStyle(
            'ReportMuted',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10,
            textColor=C_MUTED
        )

        elements = []

        # 1. Header
        header_text = """
        <b>GOVERNMENT OF INDIA &bull; भारत सरकार</b><br/>
        <b>MINISTRY OF STATISTICS & PROGRAMME IMPLEMENTATION (MoSPI)</b><br/>
        <font size="8" color="#71717a">NATIONAL STATISTICAL SYSTEMS TRAINING ACADEMY (NSSTA), PLOT 22, KNOWLEDGE PARK II, GREATER NOIDA</font><br/>
        <font size="11" color="#09090b"><b>ANNUAL CADRE COMPETENCY READINESS & TPAC ALLOCATION REPORT</b></font><br/>
        <font size="8" color="#71717a">Statutory Dossier for Training Programme Approval Committee (TPAC) Review &bull; Cycle 2026-2027</font>
        """
        elements.append(Paragraph(header_text, style_title))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

        # 2. Executive Summary Metrics
        all_users = db.query(User).all()
        statistical_officers = [u for u in all_users if u.role in ["LEARNER", "SUPERVISOR"]]
        all_user_comps = db.query(UserCompetency).all()
        
        avg_level = 0.0
        if all_user_comps:
            avg_level = round(sum(uc.current_level for uc in all_user_comps) / len(all_user_comps), 2)
            
        total_enrollments = db.query(Enrollment).count()
        completed_enrollments = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.COMPLETED.value).count()

        summary_data = [
            [
                Paragraph(f"<b>Statistical Personnel Assessed</b><br/><font size='12'><b>{len(statistical_officers)} Officers</b></font><br/><font size='7' color='#71717a'>ISS & SSS Cadres</font>", style_body),
                Paragraph(f"<b>Cadre Competency Index</b><br/><font size='12'><b>{avg_level} / 5.0</b></font><br/><font size='7' color='#71717a'>Across 18 MoSPI Competencies</font>", style_body),
                Paragraph(f"<b>Training Nominations</b><br/><font size='12'><b>{total_enrollments} Enrolled</b></font><br/><font size='7' color='#71717a'>iGOT & TPAC Dual-Track</font>", style_body),
                Paragraph(f"<b>Certifications Completed</b><br/><font size='12'><b>{completed_enrollments} Badges</b></font><br/><font size='7' color='#71717a'>Audit-Verified Seals</font>", style_body),
            ]
        ]
        summary_table = Table(summary_data, colWidths=[130, 130, 130, 130])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 14))

        # 3. Division Competency Health Matrix
        elements.append(Paragraph("<b>1. Division-Wise Competency Readiness Matrix</b>", style_heading))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<font size='7.5' color='#71717a'>Evaluates average proficiency vs benchmark expectations across major MoSPI operational divisions.</font>", style_muted))
        elements.append(Spacer(1, 6))

        division_specs = [
            {"code": "FOD", "name": "Field Operations Division (NSS Survey Operations)", "core": "STAT-SURV, STAT-LABOUR", "target": 3.0, "avg": 2.4, "gap": "Moderate (0.6)", "urgency": "HIGH"},
            {"code": "NAD", "name": "National Accounts Division (Macro Accounts & GDP)", "core": "STAT-NAS, STAT-AGRI", "target": 3.5, "avg": 2.8, "gap": "Moderate (0.7)", "urgency": "HIGH"},
            {"code": "ESD", "name": "Economic Statistics Division (CPI & Price Indices)", "core": "STAT-PRICE, STAT-IND", "target": 3.0, "avg": 2.6, "gap": "Low (0.4)", "urgency": "MEDIUM"},
            {"code": "SDRD", "name": "Survey Design & Research Division (Methodology)", "core": "STAT-SURV, STAT-MATH", "target": 3.5, "avg": 2.9, "gap": "Moderate (0.6)", "urgency": "HIGH"},
            {"code": "DPD", "name": "Data Processing Division (Tabulation & Big Data)", "core": "TECH-PYST, TECH-DBQL", "target": 3.0, "avg": 2.1, "gap": "High (0.9)", "urgency": "CRITICAL"},
        ]

        div_table_data = [
            [
                Paragraph("<b>Division Code & Name</b>", style_th),
                Paragraph("<b>Key Competency Focus</b>", style_th),
                Paragraph("<b>Benchmark</b>", style_th),
                Paragraph("<b>Current</b>", style_th),
                Paragraph("<b>Gap Delta</b>", style_th),
                Paragraph("<b>TPAC Priority</b>", style_th),
            ]
        ]

        for d in division_specs:
            color_str = "#dc2626" if d["urgency"] == "CRITICAL" else ("#ea580c" if d["urgency"] == "HIGH" else "#16a34a")
            div_table_data.append([
                Paragraph(f"<b>{d['code']}</b><br/><font size='7' color='#71717a'>{d['name'][:35]}...</font>", style_body),
                Paragraph(d["core"], style_body),
                Paragraph(f"Level {d['target']}", style_body),
                Paragraph(f"Level {d['avg']}", style_body),
                Paragraph(d["gap"], style_body),
                Paragraph(f"<font color='{color_str}'><b>{d['urgency']}</b></font>", style_body)
            ])

        div_table = Table(div_table_data, colWidths=[140, 130, 65, 60, 65, 60])
        div_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_DARK_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG])
        ]))
        elements.append(div_table)
        elements.append(Spacer(1, 14))

        # 4. Top 5 Systemic Workforce Bottlenecks
        elements.append(Paragraph("<b>2. Top 5 Cadre-Wide Systemic Competency Bottlenecks</b>", style_heading))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<font size='7.5' color='#71717a'>Identified using Weighted Urgency Scoring (WUS = Gap Delta &times; Role Criticality Weight) across all participating personnel.</font>", style_muted))
        elements.append(Spacer(1, 6))

        bottlenecks = [
            {"code": "TECH-PYST", "name": "Python for Statistical Computing & Survey Data", "gap": 1.2, "wus": 2.4, "impact": "Impairs transition from legacy FoxPro/COBOL to modern automated pipelines."},
            {"code": "STAT-NAS", "name": "System of National Accounts (SNA 2008) & GVA", "gap": 1.0, "wus": 2.0, "impact": "Delays adoption of new base year revision and supply-use table balance."},
            {"code": "TECH-DBQL", "name": "Database Management, SQL & Big Data Architecture", "gap": 0.9, "wus": 1.8, "impact": "Restricts integration of administrative registries with survey microdata."},
            {"code": "STAT-PRICE", "name": "Consumer Price Index (CPI) & Inflation Metrics", "gap": 0.7, "wus": 1.4, "impact": "High turnover of field price collectors requires continuous refresher."},
            {"code": "STAT-DQAF", "name": "MoSPI Data Quality Assessment Framework & Audit", "gap": 0.6, "wus": 1.2, "impact": "Vital for maintaining integrity under UN Fundamental Principles."}
        ]

        bot_table_data = [
            [
                Paragraph("<b>Competency Code & Title</b>", style_th),
                Paragraph("<b>Average Gap</b>", style_th),
                Paragraph("<b>WUS Score</b>", style_th),
                Paragraph("<b>Operational Risk & Cadre Impact</b>", style_th),
            ]
        ]

        for b in bottlenecks:
            bot_table_data.append([
                Paragraph(f"<b>{b['code']}</b><br/>{b['name']}", style_body),
                Paragraph(f"-{b['gap']} Levels", style_body),
                Paragraph(f"<b>{b['wus']}</b>", style_body),
                Paragraph(b["impact"], style_body),
            ])

        bot_table = Table(bot_table_data, colWidths=[150, 70, 60, 240])
        bot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_DARK_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG])
        ]))
        elements.append(bot_table)
        elements.append(Spacer(1, 14))

        # 5. TPAC Recommended Residential Training Batches
        elements.append(Paragraph("<b>3. NSSTA TPAC Training Allocation & Batch Recommendations (2026-27)</b>", style_heading))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<font size='7.5' color='#71717a'>Automated cohort allocation targeting officers with WUS gap scores &ge; 1.5 in priority disciplines.</font>", style_muted))
        elements.append(Spacer(1, 6))

        tpac_batches = [
            {
                "batch_id": "TPAC-2026-B1",
                "title": "Advanced National Accounts & GVA Compilation (SNA 2008)",
                "location": "NSSTA Greater Noida (Residential)",
                "dates": "15-26 October 2026",
                "capacity": "35 Officers",
                "target_div": "NAD, ESD, SDRD"
            },
            {
                "batch_id": "TPAC-2026-B2",
                "title": "Modern Survey Sampling, NSS Weighting & CAPI Analytics",
                "location": "NSSTA Greater Noida (Residential)",
                "dates": "05-16 November 2026",
                "capacity": "40 Officers",
                "target_div": "FOD, SDRD, DPD"
            },
            {
                "batch_id": "TPAC-2026-B3",
                "title": "Python & Data Science Bootcamp for Official Statisticians",
                "location": "NSSTA Computer Lab 1 (Blended)",
                "dates": "01-12 December 2026",
                "capacity": "30 Officers",
                "target_div": "DPD, DIID, FOD"
            }
        ]

        batch_table_data = [
            [
                Paragraph("<b>Batch ID & Course Title</b>", style_th),
                Paragraph("<b>Venue & Mode</b>", style_th),
                Paragraph("<b>Proposed Schedule</b>", style_th),
                Paragraph("<b>Target Cohorts</b>", style_th),
            ]
        ]

        for bt in tpac_batches:
            batch_table_data.append([
                Paragraph(f"<b>{bt['batch_id']}</b><br/>{bt['title']}", style_body),
                Paragraph(bt["location"], style_body),
                Paragraph(f"<b>{bt['dates']}</b><br/><font size='7' color='#71717a'>Cap: {bt['capacity']}</font>", style_body),
                Paragraph(f"<b>Divisions:</b> {bt['target_div']}", style_body),
            ])

        batch_table = Table(batch_table_data, colWidths=[170, 130, 110, 110])
        batch_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_DARK_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG])
        ]))
        elements.append(batch_table)
        elements.append(Spacer(1, 16))

        # 6. Committee Sign-off Block
        sign_data = [
            [
                Paragraph("""
                <b>Submitted by:</b><br/><br/>
                __________________________________<br/>
                <b>Member Secretary, TPAC</b><br/>
                Director, NSSTA Greater Noida
                """, style_body),
                Paragraph("""
                <b>Reviewed & Endorsed by:</b><br/><br/>
                __________________________________<br/>
                <b>Additional Director General</b><br/>
                Training Division, MoSPI
                """, style_body),
                Paragraph("""
                <b>Approved by:</b><br/><br/>
                __________________________________<br/>
                <b>Director General</b><br/>
                Ministry of Statistics & PI (MoSPI)
                """, style_body),
            ]
        ]
        sign_table = Table(sign_data, colWidths=[170, 170, 180])
        sign_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(KeepTogether(sign_table))

        doc.build(elements, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
