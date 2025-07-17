import logging
from typing import Optional
import PyPDF2
import io

logger = logging.getLogger(__name__)

class PDFUtils:
    """Utility functions for PDF processing"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> str:
        """
        Extract text from PDF using PyPDF2
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text as string
        """
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
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    @staticmethod
    def get_pdf_metadata(pdf_content: bytes) -> dict:
        """
        Extract metadata from PDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            metadata = {}
            
            # Get basic info
            metadata['num_pages'] = len(pdf_reader.pages)
            
            # Get document info if available
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                metadata['title'] = doc_info.get('/Title', '')
                metadata['author'] = doc_info.get('/Author', '')
                metadata['subject'] = doc_info.get('/Subject', '')
                metadata['creator'] = doc_info.get('/Creator', '')
                metadata['producer'] = doc_info.get('/Producer', '')
                metadata['creation_date'] = doc_info.get('/CreationDate', '')
                metadata['modification_date'] = doc_info.get('/ModDate', '')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {str(e)}")
            return {}
    
    @staticmethod
    def is_valid_pdf(pdf_content: bytes) -> bool:
        """
        Check if content is a valid PDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            # Try to access pages to validate
            _ = len(pdf_reader.pages)
            return True
            
        except Exception as e:
            logger.warning(f"Invalid PDF content: {str(e)}")
            return False
    
    @staticmethod
    def extract_text_with_positions(pdf_content: bytes) -> list:
        """
        Extract text with position information (basic implementation)
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            List of text elements with position info
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_elements = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # PyPDF2 doesn't provide detailed position info
                    # This is a basic implementation
                    page_text = page.extract_text()
                    if page_text:
                        text_elements.append({
                            'page': page_num + 1,
                            'text': page_text,
                            'position': None  # Would need more advanced library for positions
                        })
                except Exception as e:
                    logger.warning(f"Error extracting positioned text from page {page_num}: {str(e)}")
                    continue
            
            return text_elements
            
        except Exception as e:
            logger.error(f"Error extracting positioned text: {str(e)}")
            return []
