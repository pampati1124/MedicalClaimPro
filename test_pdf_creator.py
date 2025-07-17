#!/usr/bin/env python3
"""
Simple script to create test PDF files for the medical insurance claim processor
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os

def create_test_bill_pdf():
    """Create a sample medical bill PDF"""
    filename = "test_medical_bill.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title
    title = Paragraph("ABC General Hospital", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Hospital info
    hospital_info = Paragraph("123 Medical Drive<br/>Healthcare City, HC 12345<br/>Phone: (555) 123-4567", styles['Normal'])
    story.append(hospital_info)
    story.append(Spacer(1, 12))
    
    # Bill header
    bill_header = Paragraph("MEDICAL BILL", styles['Heading1'])
    story.append(bill_header)
    story.append(Spacer(1, 12))
    
    # Patient info
    patient_info = Paragraph("""
    <b>Patient:</b> John Smith<br/>
    <b>Patient ID:</b> P123456<br/>
    <b>Date of Service:</b> 2024-01-15<br/>
    <b>Account Number:</b> ACC-789456
    """, styles['Normal'])
    story.append(patient_info)
    story.append(Spacer(1, 12))
    
    # Services
    services = Paragraph("""
    <b>Services Provided:</b><br/>
    • Emergency Room Visit - $250.00<br/>
    • X-Ray Chest - $150.00<br/>
    • Laboratory Tests - $75.00<br/>
    • Physician Consultation - $200.00<br/>
    <br/>
    <b>Total Amount: $675.00</b>
    """, styles['Normal'])
    story.append(services)
    
    doc.build(story)
    print(f"Created {filename}")
    return filename

def create_test_discharge_pdf():
    """Create a sample discharge summary PDF"""
    filename = "test_discharge_summary.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title
    title = Paragraph("Hospital Discharge Summary", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Patient info
    patient_info = Paragraph("""
    <b>Patient Name:</b> John Smith<br/>
    <b>Patient ID:</b> P123456<br/>
    <b>Admission Date:</b> 2024-01-15<br/>
    <b>Discharge Date:</b> 2024-01-17<br/>
    <b>Attending Physician:</b> Dr. Sarah Johnson
    """, styles['Normal'])
    story.append(patient_info)
    story.append(Spacer(1, 12))
    
    # Diagnosis
    diagnosis = Paragraph("""
    <b>Primary Diagnosis:</b> Acute Appendicitis<br/>
    <b>Secondary Diagnosis:</b> Dehydration
    """, styles['Normal'])
    story.append(diagnosis)
    story.append(Spacer(1, 12))
    
    # Treatment
    treatment = Paragraph("""
    <b>Treatment Summary:</b><br/>
    Patient underwent laparoscopic appendectomy on 2024-01-15. 
    Surgery was successful with no complications. Patient recovered well 
    and was discharged in stable condition.
    """, styles['Normal'])
    story.append(treatment)
    story.append(Spacer(1, 12))
    
    # Medications
    medications = Paragraph("""
    <b>Discharge Medications:</b><br/>
    • Amoxicillin 500mg - Take twice daily for 7 days<br/>
    • Ibuprofen 400mg - Take as needed for pain
    """, styles['Normal'])
    story.append(medications)
    
    doc.build(story)
    print(f"Created {filename}")
    return filename

def create_test_id_card_pdf():
    """Create a sample ID card PDF"""
    filename = "test_id_card.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title
    title = Paragraph("Patient ID Card", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Card info
    card_info = Paragraph("""
    <b>HEALTHCARE INSURANCE CARD</b><br/><br/>
    <b>Patient Name:</b> John Smith<br/>
    <b>Patient ID:</b> P123456<br/>
    <b>Date of Birth:</b> 1985-03-20<br/>
    <b>Address:</b> 456 Oak Street, Anytown, AT 67890<br/>
    <b>Phone:</b> (555) 987-6543<br/>
    <b>Emergency Contact:</b> Jane Smith (555) 987-6544<br/><br/>
    <b>Insurance Provider:</b> HealthCare Plus<br/>
    <b>Policy Number:</b> HP-987654321<br/>
    <b>Group Number:</b> GRP-555<br/>
    <b>Member ID:</b> M123456789<br/>
    <b>Effective Date:</b> 2024-01-01<br/>
    <b>Expiration Date:</b> 2024-12-31
    """, styles['Normal'])
    story.append(card_info)
    
    doc.build(story)
    print(f"Created {filename}")
    return filename

if __name__ == "__main__":
    try:
        bill_file = create_test_bill_pdf()
        discharge_file = create_test_discharge_pdf()
        id_card_file = create_test_id_card_pdf()
        
        print(f"\nTest files created successfully:")
        print(f"- {bill_file}")
        print(f"- {discharge_file}")
        print(f"- {id_card_file}")
        
    except Exception as e:
        print(f"Error creating test files: {e}")