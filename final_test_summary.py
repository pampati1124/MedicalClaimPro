#!/usr/bin/env python3
import requests
import json

def test_final_validation():
    print("=== FINAL INSURANCE VALIDATION TEST ===\n")
    
    # Test files
    test_files = [
        ("non_insurance_bill.pdf", "Non-Insurance Bill (Private Pay)"),
        ("insurance_bill.pdf", "Insurance Claim Bill"),
        ("test_medical_bill.pdf", "Original Test Bill")
    ]
    
    for filename, description in test_files:
        print(f"Testing: {description}")
        print(f"File: {filename}")
        
        try:
            with open(filename, 'rb') as f:
                files = {'files': f}
                response = requests.post('http://localhost:5000/process-claim', files=files)
            
            if response.status_code == 200:
                data = response.json()
                status = data['claim_decision']['status'].upper()
                reason = data['claim_decision']['reason']
                confidence = data['claim_decision']['confidence']
                
                print(f"✓ STATUS: {status}")
                print(f"✓ REASON: {reason}")
                print(f"✓ CONFIDENCE: {confidence:.2f}")
                
                if data['documents']:
                    doc = data['documents'][0]
                    insurance_details = doc['extracted_data'].get('insurance_details')
                    diagnosis_codes = doc['extracted_data'].get('diagnosis_codes', [])
                    procedure_codes = doc['extracted_data'].get('procedure_codes', [])
                    
                    print(f"✓ INSURANCE INFO: {'Yes' if insurance_details else 'No'}")
                    print(f"✓ DIAGNOSIS CODES: {len(diagnosis_codes)} found")
                    print(f"✓ PROCEDURE CODES: {len(procedure_codes)} found")
                
                # Determine if result is correct
                expected_approval = "insurance" in filename.lower()
                actual_approval = status == "APPROVED"
                
                if expected_approval == actual_approval:
                    print("✅ RESULT: CORRECT")
                else:
                    print("❌ RESULT: INCORRECT")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_final_validation()