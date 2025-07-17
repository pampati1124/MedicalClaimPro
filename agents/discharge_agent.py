import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from agents.base_agent import BaseAgent
from models.schemas import DocumentType

logger = logging.getLogger(__name__)

class DischargeExtractionSchema(BaseModel):
    """Schema for discharge summary extraction"""
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    attending_physician: Optional[str] = None
    diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = []
    treatment_summary: Optional[str] = None
    medications: List[str] = []
    procedures: List[str] = []
    discharge_instructions: Optional[str] = None
    follow_up_appointments: List[str] = []
    hospital_name: Optional[str] = None

class DischargeAgent(BaseAgent):
    """Agent specialized in processing discharge summary documents"""
    
    def __init__(self):
        super().__init__("DischargeAgent", DocumentType.DISCHARGE_SUMMARY)
    
    def _get_system_prompt(self) -> str:
        return """
        You are a medical records specialist AI. Extract structured information from hospital discharge summaries and medical reports.
        
        Focus on extracting:
        1. Patient identification information
        2. Admission and discharge dates
        3. Medical staff (attending physician, etc.)
        4. Primary and secondary diagnoses
        5. Treatment summary and procedures
        6. Medications prescribed
        7. Discharge instructions and follow-up care
        8. Hospital/facility information
        
        Be precise with medical terminology and dates. If information is not clearly stated, use null.
        For lists (medications, procedures), include all relevant items found.
        
        Respond only with valid JSON matching the specified schema.
        """
    
    def _get_user_prompt(self, text_content: str, filename: str) -> str:
        return f"""
        Extract structured data from this discharge summary document:
        
        Filename: {filename}
        
        Document Content:
        {text_content}
        
        Extract all relevant medical information according to the schema.
        """
    
    def _get_response_schema(self) -> BaseModel:
        return DischargeExtractionSchema
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean discharge summary data"""
        validated = {}
        
        # Clean text fields
        validated['patient_name'] = self._clean_text_field(data.get('patient_name'))
        validated['patient_id'] = self._clean_text_field(data.get('patient_id'))
        validated['attending_physician'] = self._clean_text_field(data.get('attending_physician'))
        validated['diagnosis'] = self._clean_text_field(data.get('diagnosis'))
        validated['treatment_summary'] = self._clean_text_field(data.get('treatment_summary'))
        validated['discharge_instructions'] = self._clean_text_field(data.get('discharge_instructions'))
        validated['hospital_name'] = self._clean_text_field(data.get('hospital_name'))
        
        # Parse dates
        validated['admission_date'] = self._parse_date(data.get('admission_date'))
        validated['discharge_date'] = self._parse_date(data.get('discharge_date'))
        
        # Handle lists
        validated['secondary_diagnoses'] = self._validate_medical_list(data.get('secondary_diagnoses', []))
        validated['medications'] = self._validate_medical_list(data.get('medications', []))
        validated['procedures'] = self._validate_medical_list(data.get('procedures', []))
        validated['follow_up_appointments'] = self._validate_medical_list(data.get('follow_up_appointments', []))
        
        return validated
    
    def _validate_medical_list(self, items: List[str]) -> List[str]:
        """Validate and clean medical lists"""
        if not isinstance(items, list):
            return []
        
        validated = []
        for item in items:
            if item and isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    validated.append(cleaned)
        
        return validated
