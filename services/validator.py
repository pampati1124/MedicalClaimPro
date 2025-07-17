import logging
from typing import List, Dict, Any, Set
from datetime import datetime

from models.schemas import ValidationResult, DocumentType

logger = logging.getLogger(__name__)

class ClaimValidator:
    """Validates processed claim data for consistency and completeness"""
    
    def __init__(self):
        # Only require a medical bill - other documents are optional
        self.required_document_types = {
            DocumentType.BILL
        }
        
        self.optional_document_types = {
            DocumentType.DISCHARGE_SUMMARY,
            DocumentType.ID_CARD,
            DocumentType.INSURANCE_CARD
        }
    
    async def validate_claim(self, processed_docs: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate processed claim documents
        
        Args:
            processed_docs: List of processed document data
            
        Returns:
            ValidationResult with validation findings
        """
        try:
            missing_documents = []
            discrepancies = []
            warnings = []
            
            # Check for missing required documents
            missing_docs = self._check_missing_documents(processed_docs)
            missing_documents.extend(missing_docs)
            
            # Check for data consistency
            consistency_issues = self._check_data_consistency(processed_docs)
            discrepancies.extend(consistency_issues)
            
            # Check for data quality issues
            quality_warnings = self._check_data_quality(processed_docs)
            warnings.extend(quality_warnings)
            
            # Check for date consistency
            date_issues = self._check_date_consistency(processed_docs)
            discrepancies.extend(date_issues)
            
            # Check for patient name consistency
            name_issues = self._check_patient_name_consistency(processed_docs)
            discrepancies.extend(name_issues)
            
            # Check for amount validation
            amount_warnings = self._check_amount_validation(processed_docs)
            warnings.extend(amount_warnings)
            
            is_valid = len(discrepancies) == 0 and len(missing_documents) == 0
            
            logger.info(f"Validation complete. Valid: {is_valid}, "
                       f"Missing: {len(missing_documents)}, "
                       f"Discrepancies: {len(discrepancies)}, "
                       f"Warnings: {len(warnings)}")
            
            return ValidationResult(
                missing_documents=missing_documents,
                discrepancies=discrepancies,
                warnings=warnings,
                is_valid=is_valid
            )
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return ValidationResult(
                missing_documents=[],
                discrepancies=[f"Validation error: {str(e)}"],
                warnings=[],
                is_valid=False
            )
    
    def _check_missing_documents(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for missing required documents"""
        missing = []
        
        present_types = set()
        for doc in processed_docs:
            doc_type = doc.get('document_type')
            if doc_type and doc.get('agent_response'):
                present_types.add(doc_type)
        
        for required_type in self.required_document_types:
            if required_type not in present_types:
                missing.append(required_type.value)
        
        return missing
    
    def _check_data_consistency(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for data consistency across documents"""
        discrepancies = []
        
        # Extract data from all documents
        extracted_data = {}
        for doc in processed_docs:
            if doc.get('agent_response') and doc['agent_response'].extracted_data:
                doc_type = doc['document_type']
                extracted_data[doc_type] = doc['agent_response'].extracted_data
        
        # Check patient names consistency
        patient_names = []
        for doc_type, data in extracted_data.items():
            if 'patient_name' in data and data['patient_name']:
                patient_names.append((doc_type.value, data['patient_name']))
        
        if len(patient_names) > 1:
            first_name = patient_names[0][1].lower().strip()
            for doc_type, name in patient_names[1:]:
                if name.lower().strip() != first_name:
                    discrepancies.append(
                        f"Patient name mismatch: {patient_names[0][1]} vs {name}"
                    )
        
        return discrepancies
    
    def _check_data_quality(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for data quality issues"""
        warnings = []
        
        for doc in processed_docs:
            if not doc.get('agent_response'):
                warnings.append(f"Failed to process document: {doc.get('filename', 'unknown')}")
                continue
            
            agent_response = doc['agent_response']
            
            # Check confidence levels
            if agent_response.confidence < 0.5:
                warnings.append(
                    f"Low confidence ({agent_response.confidence:.2f}) for {doc.get('filename', 'unknown')}"
                )
            
            # Check for processing errors
            if agent_response.errors:
                warnings.append(
                    f"Processing errors in {doc.get('filename', 'unknown')}: {', '.join(agent_response.errors)}"
                )
        
        return warnings
    
    def _check_date_consistency(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for date consistency across documents"""
        discrepancies = []
        
        # Extract relevant dates
        service_dates = []
        admission_dates = []
        discharge_dates = []
        
        for doc in processed_docs:
            if not doc.get('agent_response') or not doc['agent_response'].extracted_data:
                continue
            
            data = doc['agent_response'].extracted_data
            doc_type = doc['document_type']
            
            if doc_type == DocumentType.BILL:
                if data.get('date_of_service'):
                    service_dates.append(data['date_of_service'])
            
            elif doc_type == DocumentType.DISCHARGE_SUMMARY:
                if data.get('admission_date'):
                    admission_dates.append(data['admission_date'])
                if data.get('discharge_date'):
                    discharge_dates.append(data['discharge_date'])
        
        # Check if service date falls within admission/discharge period
        if service_dates and admission_dates and discharge_dates:
            # This is a simplified check - in practice, would need proper date parsing
            for service_date in service_dates:
                for admission_date in admission_dates:
                    for discharge_date in discharge_dates:
                        if service_date and admission_date and discharge_date:
                            # Add more sophisticated date validation here
                            pass
        
        return discrepancies
    
    def _check_patient_name_consistency(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for patient name consistency across documents"""
        discrepancies = []
        
        patient_names = []
        for doc in processed_docs:
            if not doc.get('agent_response') or not doc['agent_response'].extracted_data:
                continue
            
            data = doc['agent_response'].extracted_data
            if data.get('patient_name'):
                patient_names.append({
                    'name': data['patient_name'],
                    'document': doc.get('filename', 'unknown'),
                    'type': doc['document_type'].value
                })
        
        if len(patient_names) > 1:
            # Normalize names for comparison
            normalized_names = {}
            for name_data in patient_names:
                normalized = self._normalize_name(name_data['name'])
                if normalized not in normalized_names:
                    normalized_names[normalized] = []
                normalized_names[normalized].append(name_data)
            
            if len(normalized_names) > 1:
                names_list = list(normalized_names.keys())
                discrepancies.append(
                    f"Patient name inconsistency found: {', '.join(names_list)}"
                )
        
        return discrepancies
    
    def _check_amount_validation(self, processed_docs: List[Dict[str, Any]]) -> List[str]:
        """Check for amount validation issues"""
        warnings = []
        
        for doc in processed_docs:
            if not doc.get('agent_response') or not doc['agent_response'].extracted_data:
                continue
            
            data = doc['agent_response'].extracted_data
            doc_type = doc['document_type']
            
            if doc_type == DocumentType.BILL:
                total_amount = data.get('total_amount')
                if total_amount is None:
                    warnings.append(f"Missing total amount in bill: {doc.get('filename', 'unknown')}")
                elif total_amount <= 0:
                    warnings.append(f"Invalid total amount ({total_amount}) in bill: {doc.get('filename', 'unknown')}")
                elif total_amount > 100000:  # Arbitrary high amount threshold
                    warnings.append(f"Unusually high amount ({total_amount}) in bill: {doc.get('filename', 'unknown')}")
        
        return warnings
    
    def _normalize_name(self, name: str) -> str:
        """Normalize patient name for comparison"""
        if not name:
            return ""
        
        # Remove common prefixes/suffixes and normalize
        name = name.strip().lower()
        
        # Remove common titles
        prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        return name
