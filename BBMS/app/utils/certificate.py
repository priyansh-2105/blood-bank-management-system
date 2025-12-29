import qrcode
import uuid
from datetime import datetime
from io import BytesIO
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_certificate_id():
    """Generate unique certificate ID"""
    return f"CERT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

def create_qr_code(data):
    """Create QR code for certificate"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def generate_html_certificate(donation_record):
    """Generate HTML certificate"""
    certificate_id = generate_certificate_id()
    qr_data = f"Certificate ID: {certificate_id}\nDonor: {donation_record.donor.user.name}\nDate: {donation_record.donation_date.strftime('%B %d, %Y')}\nBlood Group: {donation_record.blood_group}\nQuantity: {donation_record.quantity} units"
    qr_code = create_qr_code(qr_data)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Blood Donation Certificate</title>
        <style>
            body {{
                font-family: 'Times New Roman', serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .certificate {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border: 3px solid #dc3545;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #dc3545;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .title {{
                color: #dc3545;
                font-size: 36px;
                font-weight: bold;
                margin: 0;
            }}
            .subtitle {{
                color: #6c757d;
                font-size: 18px;
                margin: 10px 0;
            }}
            .content {{
                text-align: center;
                margin: 40px 0;
            }}
            .donor-name {{
                font-size: 28px;
                font-weight: bold;
                color: #343a40;
                margin: 20px 0;
            }}
            .details {{
                font-size: 16px;
                line-height: 1.6;
                margin: 20px 0;
            }}
            .qr-section {{
                text-align: center;
                margin: 40px 0;
            }}
            .qr-code {{
                display: inline-block;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
            }}
            .signature {{
                margin-top: 60px;
                display: flex;
                justify-content: space-between;
            }}
            .signature-line {{
                border-top: 1px solid #000;
                width: 200px;
                text-align: center;
                padding-top: 5px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="certificate">
            <div class="header">
                <h1 class="title">🩸 Blood Bank Management System</h1>
                <p class="subtitle">Certificate of Blood Donation</p>
            </div>
            
            <div class="content">
                <p class="details">This is to certify that</p>
                <div class="donor-name">{donation_record.donor.user.name}</div>
                <p class="details">
                    has successfully donated <strong>{donation_record.quantity} units</strong> of 
                    <strong>{donation_record.blood_group}</strong> blood on 
                    <strong>{donation_record.donation_date.strftime('%B %d, %Y')}</strong>
                </p>
                <p class="details">
                    This generous act of blood donation will help save lives and contribute to the 
                    healthcare system. We sincerely appreciate this noble gesture.
                </p>
            </div>
            
            <div class="qr-section">
                <p><strong>Certificate ID:</strong> {certificate_id}</p>
                <div class="qr-code">
                    <img src="data:image/png;base64,{qr_code}" alt="QR Code" width="150" height="150">
                </div>
            </div>
            
            <div class="signature">
                <div class="signature-line">Donor Signature</div>
                <div class="signature-line">Authorized Signature</div>
            </div>
            
            <div class="footer">
                <p>This certificate is generated electronically and is valid without signature.</p>
                <p>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content, certificate_id

def generate_pdf_certificate(donation_record):
    """Generate PDF certificate"""
    certificate_id = generate_certificate_id()
    qr_data = f"Certificate ID: {certificate_id}\nDonor: {donation_record.donor.user.name}\nDate: {donation_record.donation_date.strftime('%B %d, %Y')}\nBlood Group: {donation_record.blood_group}\nQuantity: {donation_record.quantity} units"
    qr_code = create_qr_code(qr_data)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#dc3545'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6c757d'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    donor_name_style = ParagraphStyle(
        'DonorName',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#343a40'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Build PDF content
    story = []
    
    # Header
    story.append(Paragraph("🩸 Blood Bank Management System", title_style))
    story.append(Paragraph("Certificate of Blood Donation", subtitle_style))
    story.append(Spacer(1, 30))
    
    # Content
    story.append(Paragraph("This is to certify that", content_style))
    story.append(Paragraph(donation_record.donor.user.name, donor_name_style))
    story.append(Paragraph(
        f"has successfully donated <b>{donation_record.quantity} units</b> of "
        f"<b>{donation_record.blood_group}</b> blood on "
        f"<b>{donation_record.donation_date.strftime('%B %d, %Y')}</b>",
        content_style
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This generous act of blood donation will help save lives and contribute to the healthcare system. "
        "We sincerely appreciate this noble gesture.",
        content_style
    ))
    story.append(Spacer(1, 30))
    
    # Certificate ID
    story.append(Paragraph(f"<b>Certificate ID:</b> {certificate_id}", content_style))
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph(
        "This certificate is generated electronically and is valid without signature.",
        content_style
    ))
    story.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        content_style
    ))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data, certificate_id 