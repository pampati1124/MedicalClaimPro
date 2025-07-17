from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class DocumentType(str, Enum):
    BILL = "bill"
    DISCHARGE_SUMMARY = "discharge_summary"
    ID_CARD = "id_card"
    PRESCRIPTION = "prescription"
    INSURANCE_CARD = "insurance_card"
    UNKNOWN = "unknown"

class ClaimStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    REQUIRES_REVIEW = "requires_review"

class DocumentInfo(BaseModel):
    """Schema for processed document information"""
    type: DocumentType
    filename: str
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

class BillDocument(BaseModel):
    """Schema for medical bill documents"""
    type: DocumentType = DocumentType.BILL
    hospital_name: Optional[str] = None
    total_amount: Optional[float] = None
    date_of_service: Optional[str] = None
    patient_name: Optional[str] = None
    services: List[str] = Field(default_factory=list)
    insurance_details: Optional[Dict[str, Any]] = None

class DischargeDocument(BaseModel):
    """Schema for discharge summary documents"""
    type: DocumentType = DocumentType.DISCHARGE_SUMMARY
    patient_name: Optional[str] = None
    diagnosis: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    attending_physician: Optional[str] = None
    treatment_summary: Optional[str] = None
    medications: List[str] = Field(default_factory=list)

class IdCardDocument(BaseModel):
    """Schema for ID card documents"""
    type: DocumentType = DocumentType.ID_CARD
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None

class ValidationResult(BaseModel):
    """Schema for validation results"""
    missing_documents: List[str] = Field(default_factory=list)
    discrepancies: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    is_valid: bool = True

class ClaimDecision(BaseModel):
    """Schema for claim decision"""
    status: ClaimStatus
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    additional_info: Optional[str] = None
    
    class Config:
        use_enum_values = True

class ClaimProcessingResponse(BaseModel):
    """Main response schema for claim processing"""
    documents: List[DocumentInfo] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    validation: ValidationResult = Field(default_factory=ValidationResult)
    claim_decision: ClaimDecision
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AgentResponse(BaseModel):
    """Schema for agent processing responses"""
    agent_name: str
    document_type: DocumentType
    extracted_data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time: float
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
