#!/usr/bin/env python3
import requests
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io

def create_non_insurance_bill():
    """Create a medical bill WITHOUT insurance information"""
    filename = "non_insurance_bill.pdf"
    
    # Create PDF content
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    story.append(Paragraph("PRIVATE PAY MEDICAL BILL", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Hospital info
    story.append(Paragraph("XYZ Private Clinic", styles['Heading2']))
    story.append(Paragraph("789 Private Street<br/>Cash City, CC 54321", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Patient info
    story.append(Paragraph("PATIENT: Jane Doe", styles['Normal']))
    story.append(Paragraph("PAYMENT METHOD: Cash Payment", styles['Normal']))
    story.append(Paragraph("SERVICE DATE: 2024-01-20", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Services (no insurance codes)
    story.append(Paragraph("SERVICES PROVIDED:", styles['Heading3']))
    story.append(Paragraph("General Consultation - $200.00", styles['Normal']))
    story.append(Paragraph("Blood Test - $75.00", styles['Normal']))
    story.append(Paragraph("Cash Discount Applied - $25.00", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Total
    story.append(Paragraph("TOTAL AMOUNT: $250.00", styles['Heading3']))
    story.append(Paragraph("PAYMENT STATUS: PAID IN FULL", styles['Normal']))
    
    doc.build(story)
    
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    return filename

def create_insurance_bill():
    """Create a medical bill WITH insurance information"""
    filename = "insurance_bill.pdf"
    
    # Create PDF content
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    story.append(Paragraph("INSURANCE CLAIM STATEMENT", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Hospital info
    story.append(Paragraph("ABC General Hospital", styles['Heading2']))
    story.append(Paragraph("123 Medical Drive<br/>Healthcare City, HC 12345", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Patient info
    story.append(Paragraph("PATIENT: John Smith", styles['Normal']))
    story.append(Paragraph("PATIENT ID: P123456", styles['Normal']))
    story.append(Paragraph("INSURANCE: Blue Cross Blue Shield", styles['Normal']))
    story.append(Paragraph("POLICY NUMBER: BC-987654321", styles['Normal']))
    story.append(Paragraph("MEMBER ID: M123456789", styles['Normal']))
    story.append(Paragraph("SERVICE DATE: 2024-01-15", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Services with codes
    story.append(Paragraph("SERVICES PROVIDED:", styles['Heading3']))
    story.append(Paragraph("Emergency Room Visit (CPT: 99284) - $500.00", styles['Normal']))
    story.append(Paragraph("X-Ray Chest (CPT: 71020) - $150.00", styles['Normal']))
    story.append(Paragraph("Laboratory Tests (CPT: 80053) - $75.00", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Diagnosis codes
    story.append(Paragraph("DIAGNOSIS CODES:", styles['Heading3']))
    story.append(Paragraph("ICD-10: J44.1 - Chronic obstructive pulmonary disease", styles['Normal']))
    story.append(Paragraph("ICD-10: Z51.11 - Encounter for antineoplastic chemotherapy", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Insurance details
    story.append(Paragraph("INSURANCE CLAIM DETAILS:", styles['Heading3']))
    story.append(Paragraph("Total Charges: $725.00", styles['Normal']))
    story.append(Paragraph("Insurance Coverage: $650.00", styles['Normal']))
    story.append(Paragraph("Patient Copay: $25.00", styles['Normal']))
    story.append(Paragraph("Deductible Applied: $50.00", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Total
    story.append(Paragraph("PATIENT RESPONSIBILITY: $75.00", styles['Heading3']))
    
    doc.build(story)
    
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    return filename

def test_bills():
    print("Creating test bills...")
    non_insurance_file = create_non_insurance_bill()
    insurance_file = create_insurance_bill()
    
    print("=== NON-INSURANCE BILL (Should be REJECTED) ===")
    with open(non_insurance_file, 'rb') as f:
        files = {'files': f}
        response = requests.post('http://localhost:5000/process-claim', files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"STATUS: {data['claim_decision']['status'].upper()}")
        print(f"REASON: {data['claim_decision']['reason']}")
        print(f"CONFIDENCE: {data['claim_decision']['confidence']:.2f}")
        print(f"DISCREPANCIES: {data['validation']['discrepancies']}")
        print(f"WARNINGS: {data['validation']['warnings']}")
        if data['documents']:
            doc = data['documents'][0]
            print(f"INSURANCE DETAILS: {doc['extracted_data'].get('insurance_details', 'None')}")
            print(f"DIAGNOSIS CODES: {doc['extracted_data'].get('diagnosis_codes', [])}")
            print(f"PROCEDURE CODES: {doc['extracted_data'].get('procedure_codes', [])}")
    
    print("\n=== INSURANCE BILL (Should be APPROVED) ===")
    with open(insurance_file, 'rb') as f:
        files = {'files': f}
        response = requests.post('http://localhost:5000/process-claim', files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"STATUS: {data['claim_decision']['status'].upper()}")
        print(f"REASON: {data['claim_decision']['reason']}")
        print(f"CONFIDENCE: {data['claim_decision']['confidence']:.2f}")
        print(f"DISCREPANCIES: {data['validation']['discrepancies']}")
        print(f"WARNINGS: {data['validation']['warnings']}")
        if data['documents']:
            doc = data['documents'][0]
            print(f"INSURANCE DETAILS: {doc['extracted_data'].get('insurance_details', 'None')}")
            print(f"DIAGNOSIS CODES: {doc['extracted_data'].get('diagnosis_codes', [])}")
            print(f"PROCEDURE CODES: {doc['extracted_data'].get('procedure_codes', [])}")

if __name__ == "__main__":
    test_bills()