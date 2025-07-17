import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

from agents.base_agent import BaseAgent
from models.schemas import DocumentType

logger = logging.getLogger(__name__)

class IdCardExtractionSchema(BaseModel):
    """Schema for ID card extraction"""
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    insurance_provider: Optional[str] = None
    policy_number: Optional[str] = None
    group_number: Optional[str] = None
    member_id: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None

class IdCardAgent(BaseAgent):
    """Agent specialized in processing ID card and insurance card documents"""
    
    def __init__(self):
        super().__init__("IdCardAgent", DocumentType.ID_CARD)
    
    def _get_system_prompt(self) -> str:
        return """
        You are an identification document specialist AI. Extract structured information from patient ID cards, insurance cards, and identification documents.
        
        Focus on extracting:
        1. Personal identification information
        2. Contact details
        3. Insurance information (if present)
        4. Policy numbers and member IDs
        5. Effective and expiration dates
        6. Emergency contact information
        
        Be precise with identification numbers and dates. If information is not clearly stated, use null.
        Handle both medical ID cards and insurance cards.
        
        Respond only with valid JSON matching the specified schema.
        """
    
    def _get_user_prompt(self, text_content: str, filename: str) -> str:
        return f"""
        Extract structured data from this ID card document:
        
        Filename: {filename}
        
        Document Content:
        {text_content}
        
        Extract all relevant identification and insurance information according to the schema.
        """
    
    def _get_response_schema(self) -> BaseModel:
        return IdCardExtractionSchema
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean ID card data"""
        validated = {}
        
        # Clean text fields
        validated['patient_name'] = self._clean_text_field(data.get('patient_name'))
        validated['patient_id'] = self._clean_text_field(data.get('patient_id'))
        validated['address'] = self._clean_text_field(data.get('address'))
        validated['phone_number'] = self._clean_phone_number(data.get('phone_number'))
        validated['emergency_contact'] = self._clean_text_field(data.get('emergency_contact'))
        validated['insurance_provider'] = self._clean_text_field(data.get('insurance_provider'))
        validated['policy_number'] = self._clean_text_field(data.get('policy_number'))
        validated['group_number'] = self._clean_text_field(data.get('group_number'))
        validated['member_id'] = self._clean_text_field(data.get('member_id'))
        
        # Parse dates
        validated['date_of_birth'] = self._parse_date(data.get('date_of_birth'))
        validated['effective_date'] = self._parse_date(data.get('effective_date'))
        validated['expiration_date'] = self._parse_date(data.get('expiration_date'))
        
        return validated
    
    def _clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean and format phone number"""
        if not phone or not isinstance(phone, str):
            return None
        
        # Remove common phone number formatting
        cleaned = phone.strip().replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        
        # Basic validation for US phone numbers
        if len(cleaned) == 10 and cleaned.isdigit():
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned.startswith('1') and cleaned[1:].isdigit():
            return f"1-({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        
        return phone.strip() if phone.strip() else None
