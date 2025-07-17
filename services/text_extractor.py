import logging
import os
from typing import Dict, Any
import PyPDF2
import io
from google import genai
from google.genai import types
from pydantic import BaseModel

from utils.json_parser import safe_json_parse

logger = logging.getLogger(__name__)

class TextExtractionResult(BaseModel):
    """Schema for text extraction result"""
    raw_text: str
    cleaned_text: str
    metadata: Dict[str, Any]
    extraction_method: str

class TextExtractor:
    """Text extraction service using PyPDF2 and Gemini for enhancement"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    async def extract_text_from_pdf(self, pdf_content: bytes, filename: str) -> str:
        """
        Extract and clean text from PDF
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            Extracted and cleaned text
        """
        try:
            # Primary extraction using PyPDF2
            raw_text = self._extract_with_pypdf2(pdf_content)
            
            if not raw_text.strip():
                logger.warning(f"No text extracted from {filename}")
                return ""
            
            # Enhance extraction with Gemini if needed
            if len(raw_text) < 100 or self._is_low_quality_text(raw_text):
                logger.info(f"Enhancing text extraction for {filename} with Gemini")
                enhanced_text = await self._enhance_with_gemini(raw_text, filename)
                return enhanced_text if enhanced_text else raw_text
            
            return raw_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return ""
    
    def _extract_with_pypdf2(self, pdf_content: bytes) -> str:
        """Extract text using PyPDF2"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return ""
    
    def _is_low_quality_text(self, text: str) -> bool:
        """Check if extracted text quality is low"""
        if not text:
            return True
        
        # Check for garbled text indicators
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        
        # Check for very short lines (possible formatting issues)
        lines = text.split('\n')
        short_lines = sum(1 for line in lines if len(line.strip()) < 3)
        
        return (
            special_char_ratio > 0.3 or
            short_lines > len(lines) * 0.5 or
            len(text.strip()) < 50
        )
    
    async def _enhance_with_gemini(self, raw_text: str, filename: str) -> str:
        """Use Gemini to enhance/clean extracted text"""
        try:
            system_prompt = """
            You are a text enhancement specialist. The following text was extracted from a medical document PDF but may contain formatting issues, OCR errors, or garbled text.
            
            Please:
            1. Clean up the text by fixing obvious OCR errors
            2. Improve formatting and structure
            3. Preserve all important medical information
            4. Return only the cleaned text, no explanations
            
            If the text is completely unreadable, return "UNREADABLE_DOCUMENT"
            """
            
            user_prompt = f"Clean and enhance this medical document text:\n\n{raw_text}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1
                )
            )
            
            enhanced_text = response.text or ""
            
            if enhanced_text and enhanced_text != "UNREADABLE_DOCUMENT":
                logger.info(f"Successfully enhanced text for {filename}")
                return enhanced_text
            else:
                logger.warning(f"Gemini could not enhance text for {filename}")
                return raw_text
                
        except Exception as e:
            logger.error(f"Error enhancing text with Gemini: {str(e)}")
            return raw_text
