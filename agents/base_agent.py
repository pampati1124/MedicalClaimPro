import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

from models.schemas import DocumentType, AgentResponse
from utils.json_parser import safe_json_parse

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all document processing agents"""
    
    def __init__(self, agent_name: str, document_type: DocumentType):
        self.agent_name = agent_name
        self.document_type = document_type
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    async def process_document(self, text_content: str, filename: str) -> AgentResponse:
        """
        Process document and return structured data
        
        Args:
            text_content: Extracted text from document
            filename: Original filename
            
        Returns:
            AgentResponse with extracted data
        """
        start_time = time.time()
        errors = []
        
        try:
            logger.info(f"{self.agent_name} processing {filename}")
            
            # Get processing prompt and schema
            system_prompt = self._get_system_prompt()
            user_prompt = self._get_user_prompt(text_content, filename)
            response_schema = self._get_response_schema()
            
            # Make API request
            extracted_data = await self._make_gemini_request(
                system_prompt, user_prompt, response_schema
            )
            
            # Validate extracted data
            validated_data = self._validate_extracted_data(extracted_data)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                agent_name=self.agent_name,
                document_type=self.document_type,
                extracted_data=validated_data,
                confidence=self._calculate_confidence(validated_data),
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in {self.agent_name} processing {filename}: {str(e)}")
            errors.append(str(e))
            
            return AgentResponse(
                agent_name=self.agent_name,
                document_type=self.document_type,
                extracted_data={},
                confidence=0.0,
                processing_time=time.time() - start_time,
                errors=errors
            )
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        pass
    
    @abstractmethod
    def _get_user_prompt(self, text_content: str, filename: str) -> str:
        """Get user prompt for the agent"""
        pass
    
    @abstractmethod
    def _get_response_schema(self) -> BaseModel:
        """Get Pydantic schema for structured response"""
        pass
    
    @abstractmethod
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        pass
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data completeness"""
        if not data:
            return 0.0
        
        # Count non-null values
        non_null_count = sum(1 for v in data.values() if v is not None and v != "")
        total_fields = len(data)
        
        if total_fields == 0:
            return 0.0
        
        base_confidence = non_null_count / total_fields
        
        # Adjust for data quality
        if any(isinstance(v, list) and len(v) > 0 for v in data.values()):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def _make_gemini_request(self, system_prompt: str, user_prompt: str, response_schema: BaseModel) -> Dict[str, Any]:
        """Make structured request to Gemini API"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1
                )
            )
            
            raw_response = response.text or ""
            
            # Parse JSON response
            parsed_data = safe_json_parse(raw_response)
            if not parsed_data:
                logger.warning(f"Failed to parse JSON response from {self.agent_name}")
                return {}
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Gemini API request failed in {self.agent_name}: {str(e)}")
            return {}
    
    def _clean_text_field(self, text: str) -> Optional[str]:
        """Clean and normalize text field"""
        if not text or not isinstance(text, str):
            return None
        
        cleaned = text.strip()
        return cleaned if cleaned else None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse monetary amount from string"""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and spaces
            cleaned = str(amount_str).replace('$', '').replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse and normalize date string"""
        if not date_str:
            return None
        
        # Return as-is for now, could add date validation/normalization
        return str(date_str).strip()
