import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from models.schemas import DocumentType

logger = logging.getLogger(__name__)

class BillExtractionSchema(BaseModel):
    """Schema for bill document extraction"""
    hospital_name: Optional[str] = None
    total_amount: Optional[float] = None
    date_of_service: Optional[str] = None
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    services: List[str] = []
    insurance_details: Optional[str] = None
    billing_address: Optional[str] = None
    account_number: Optional[str] = None
    diagnosis_codes: List[str] = []
    procedure_codes: List[str] = []

class BillAgent(BaseAgent):
    """Agent specialized in processing medical bill documents"""
    
    def __init__(self):
        super().__init__("BillAgent", DocumentType.BILL)
    
    def _get_system_prompt(self) -> str:
        return """
        You are a medical billing specialist AI. Extract structured information from medical bills, invoices, and payment statements.
        
        Focus on extracting:
        1. Hospital/provider information
        2. Patient details
        3. Service dates and descriptions
        4. Amounts and charges
        5. Insurance information
        6. Medical codes (ICD, CPT)
        7. Account/billing details
        
        Be precise with numerical values and dates. If information is not clearly stated, use null.
        For lists (services, codes), include all relevant items found.
        
        Respond only with valid JSON matching the specified schema.
        """
    
    def _get_user_prompt(self, text_content: str, filename: str) -> str:
        return f"""
        Extract structured data from this medical bill document:
        
        Filename: {filename}
        
        Document Content:
        {text_content}
        
        Extract all relevant billing information according to the schema.
        """
    
    def _get_response_schema(self) -> BaseModel:
        return BillExtractionSchema
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean bill data"""
        validated = {}
        
        # Clean text fields
        validated['hospital_name'] = self._clean_text_field(data.get('hospital_name'))
        validated['patient_name'] = self._clean_text_field(data.get('patient_name'))
        validated['patient_id'] = self._clean_text_field(data.get('patient_id'))
        validated['billing_address'] = self._clean_text_field(data.get('billing_address'))
        validated['account_number'] = self._clean_text_field(data.get('account_number'))
        
        # Parse monetary amount
        validated['total_amount'] = self._parse_amount(data.get('total_amount'))
        
        # Parse date
        validated['date_of_service'] = self._parse_date(data.get('date_of_service'))
        
        # Handle lists
        validated['services'] = self._validate_services(data.get('services', []))
        validated['diagnosis_codes'] = self._validate_codes(data.get('diagnosis_codes', []))
        validated['procedure_codes'] = self._validate_codes(data.get('procedure_codes', []))
        
        # Handle insurance details as string
        validated['insurance_details'] = self._clean_text_field(data.get('insurance_details'))
        
        return validated
    
    def _validate_services(self, services: List[str]) -> List[str]:
        """Validate and clean services list"""
        if not isinstance(services, list):
            return []
        
        validated = []
        for service in services:
            if service and isinstance(service, str):
                cleaned = service.strip()
                if cleaned:
                    validated.append(cleaned)
        
        return validated
    
    def _validate_codes(self, codes: List[str]) -> List[str]:
        """Validate medical codes"""
        if not isinstance(codes, list):
            return []
        
        validated = []
        for code in codes:
            if code and isinstance(code, str):
                cleaned = code.strip().upper()
                if cleaned:
                    validated.append(cleaned)
        
        return validated
    
    def _validate_insurance_details(self, insurance_data: Any) -> Optional[Dict[str, Any]]:
        """Validate insurance details"""
        if not insurance_data or not isinstance(insurance_data, dict):
            return None
        
        validated = {}
        for key, value in insurance_data.items():
            if value is not None:
                validated[key] = str(value).strip() if isinstance(value, str) else value
        
        return validated if validated else None
