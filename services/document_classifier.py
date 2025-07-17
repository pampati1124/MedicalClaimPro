import logging
from typing import List, Tuple
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

from models.schemas import DocumentType
from utils.json_parser import safe_json_parse

logger = logging.getLogger(__name__)

class DocumentClassification(BaseModel):
    """Schema for document classification result"""
    document_type: str
    confidence: float
    reasoning: str

class DocumentClassifier:
    """AI-powered document classifier using Gemini"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
    async def classify_document(self, text_content: str, filename: str) -> Tuple[DocumentType, float]:
        """
        Classify document based on content and filename
        
        Args:
            text_content: Extracted text from document
            filename: Original filename of the document
            
        Returns:
            Tuple of (DocumentType, confidence_score)
        """
        try:
            system_prompt = """
            You are a medical document classifier. Analyze the provided document text and filename to classify it into one of these categories:
            - bill: Medical bills, invoices, payment statements
            - discharge_summary: Hospital discharge summaries, medical reports
            - id_card: Patient ID cards, insurance cards, identification documents
            - prescription: Prescription documents, medication lists
            - insurance_card: Insurance cards, policy documents
            - unknown: If the document doesn't fit any category
            
            Consider both the filename and content. Look for key indicators:
            - Bills: amounts, charges, hospital billing, invoice numbers
            - Discharge: admission/discharge dates, diagnosis, treatment plans
            - ID Cards: patient information, ID numbers, addresses
            - Prescriptions: medication names, dosages, pharmacy information
            
            Respond with JSON containing:
            {
                "document_type": "one of the categories above",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation of classification"
            }
            """
            
            user_prompt = f"""
            Filename: {filename}
            
            Document Content:
            {text_content[:2000]}...
            
            Classify this document.
            """
            
            response = await self._make_gemini_request(system_prompt, user_prompt)
            
            # Parse response
            parsed_data = safe_json_parse(response)
            if not parsed_data:
                logger.warning(f"Failed to parse classification response for {filename}")
                return self._classify_by_filename(filename)
            
            # Map to DocumentType enum
            doc_type_str = parsed_data.get('document_type', 'unknown')
            confidence = parsed_data.get('confidence', 0.5)
            
            try:
                document_type = DocumentType(doc_type_str)
            except ValueError:
                logger.warning(f"Unknown document type: {doc_type_str}")
                document_type = DocumentType.UNKNOWN
                confidence = 0.3
            
            logger.info(f"Classified {filename} as {document_type} with confidence {confidence}")
            return document_type, confidence
            
        except Exception as e:
            logger.error(f"Error classifying document {filename}: {str(e)}")
            return self._classify_by_filename(filename)
    
    def _classify_by_filename(self, filename: str) -> Tuple[DocumentType, float]:
        """Fallback classification based on filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['bill', 'invoice', 'payment', 'charge']):
            return DocumentType.BILL, 0.6
        elif any(word in filename_lower for word in ['discharge', 'summary', 'report']):
            return DocumentType.DISCHARGE_SUMMARY, 0.6
        elif any(word in filename_lower for word in ['id', 'card', 'identity']):
            return DocumentType.ID_CARD, 0.6
        elif any(word in filename_lower for word in ['prescription', 'medication', 'rx']):
            return DocumentType.PRESCRIPTION, 0.6
        elif any(word in filename_lower for word in ['insurance', 'policy']):
            return DocumentType.INSURANCE_CARD, 0.6
        else:
            return DocumentType.UNKNOWN, 0.3
    
    async def _make_gemini_request(self, system_prompt: str, user_prompt: str) -> str:
        """Make request to Gemini API"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=DocumentClassification,
                    temperature=0.1
                )
            )
            
            return response.text or ""
            
        except Exception as e:
            logger.error(f"Gemini API request failed: {str(e)}")
            raise e
