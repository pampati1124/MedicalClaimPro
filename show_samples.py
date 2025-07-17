#!/usr/bin/env python3
import requests
import json

def test_accepted_sample():
    print("=== ACCEPTED SAMPLE ===")
    print("Testing with valid medical bill:")
    
    with open('test_medical_bill.pdf', 'rb') as f:
        files = {'files': f}
        response = requests.post('http://localhost:5000/process-claim', files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"STATUS: {data['claim_decision']['status'].upper()}")
        print(f"REASON: {data['claim_decision']['reason']}")
        print(f"CONFIDENCE: {data['claim_decision']['confidence']:.2f}")
        print(f"VALIDATION VALID: {data['validation']['is_valid']}")
        print(f"MISSING DOCS: {data['validation']['missing_documents']}")
        print(f"DISCREPANCIES: {data['validation']['discrepancies']}")
        print(f"WARNINGS: {data['validation']['warnings']}")
        print("EXTRACTED DATA:")
        for doc in data['documents']:
            print(f"  - {doc['type']}: {doc['filename']}")
            if doc['extracted_data'].get('hospital_name'):
                print(f"    Hospital: {doc['extracted_data']['hospital_name']}")
            if doc['extracted_data'].get('total_amount'):
                print(f"    Amount: ${doc['extracted_data']['total_amount']}")
    else:
        print(f"Error: {response.status_code}")

def test_rejected_sample():
    print("\n=== REJECTED SAMPLE ===")
    print("Testing with corrupted/invalid PDF:")
    
    # Create a fake corrupted PDF file
    with open('corrupted.pdf', 'wb') as f:
        f.write(b'This is not a valid PDF file content')
    
    with open('corrupted.pdf', 'rb') as f:
        files = {'files': f}
        response = requests.post('http://localhost:5000/process-claim', files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"STATUS: {data['claim_decision']['status'].upper()}")
        print(f"REASON: {data['claim_decision']['reason']}")
        print(f"CONFIDENCE: {data['claim_decision']['confidence']:.2f}")
        print(f"VALIDATION VALID: {data['validation']['is_valid']}")
        print(f"MISSING DOCS: {data['validation']['missing_documents']}")
        print(f"DISCREPANCIES: {data['validation']['discrepancies']}")
        print(f"WARNINGS: {data['validation']['warnings']}")
        if data['documents']:
            print("EXTRACTED DATA:")
            for doc in data['documents']:
                print(f"  - {doc['type']}: {doc['filename']}")
                if doc.get('extracted_data'):
                    print(f"    Data: {doc['extracted_data']}")
        else:
            print("No documents processed successfully")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_accepted_sample()
    test_rejected_sample()