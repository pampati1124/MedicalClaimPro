import asyncio
import logging
import time
from typing import List, Dict, Any
from fastapi import UploadFile

from models.schemas import (
    ClaimProcessingResponse, DocumentInfo, ValidationResult, 
    ClaimDecision, ClaimStatus, DocumentType
)
from services.document_classifier import DocumentClassifier
from services.text_extractor import TextExtractor
from services.validator import ClaimValidator
from agents.bill_agent import BillAgent
from agents.discharge_agent import DischargeAgent
from agents.id_card_agent import IdCardAgent

logger = logging.getLogger(__name__)

class ClaimProcessor:
    """Main orchestrator for claim processing workflow"""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.text_extractor = TextExtractor()
        self.validator = ClaimValidator()
        
        # Initialize agents
        self.agents = {
            DocumentType.BILL: BillAgent(),
            DocumentType.DISCHARGE_SUMMARY: DischargeAgent(),
            DocumentType.ID_CARD: IdCardAgent(),
            DocumentType.INSURANCE_CARD: IdCardAgent(),  # Reuse ID card agent
        }
    
    async def process_claim_documents(self, files: List[UploadFile]) -> ClaimProcessingResponse:
        """
        Process multiple documents for insurance claim
        
        Args:
            files: List of uploaded PDF files
            
        Returns:
            ClaimProcessingResponse with structured results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting claim processing for {len(files)} files")
            
            # Step 1: Extract text from all documents
            document_texts = await self._extract_texts(files)
            
            # Step 2: Classify documents
            classified_docs = await self._classify_documents(document_texts)
            
            # Step 3: Process documents with specialized agents
            processed_docs = await self._process_with_agents(classified_docs)
            
            # Step 4: Validate and cross-check data
            validation_result = await self._validate_claim_data(processed_docs)
            
            # Step 5: Make claim decision
            claim_decision = await self._make_claim_decision(processed_docs, validation_result)
            
            # Step 6: Structure final response
            documents_info = self._create_documents_info(processed_docs)
            structured_data = self._create_structured_data(processed_docs)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Claim processing completed in {processing_time:.2f} seconds")
            
            return ClaimProcessingResponse(
                documents=documents_info,
                structured_data=structured_data,
                validation=validation_result,
                claim_decision=claim_decision,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in claim processing: {str(e)}")
            
            # Return error response
            return ClaimProcessingResponse(
                documents=[],
                structured_data={},
                validation=ValidationResult(
                    is_valid=False,
                    missing_documents=["processing_error"],
                    discrepancies=[f"Processing failed: {str(e)}"]
                ),
                claim_decision=ClaimDecision(
                    status=ClaimStatus.REJECTED,
                    reason=f"Processing error: {str(e)}",
                    confidence=0.0
                ),
                processing_time=time.time() - start_time
            )
    
    async def _extract_texts(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Extract text from all uploaded files"""
        document_texts = []
        
        for file in files:
            try:
                content = await file.read()
                text = await self.text_extractor.extract_text_from_pdf(content, file.filename)
                
                document_texts.append({
                    'filename': file.filename,
                    'content': content,
                    'text': text
                })
                
            except Exception as e:
                logger.error(f"Error extracting text from {file.filename}: {str(e)}")
                document_texts.append({
                    'filename': file.filename,
                    'content': b'',
                    'text': '',
                    'error': str(e)
                })
        
        return document_texts
    
    async def _classify_documents(self, document_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify all documents"""
        classified_docs = []
        
        for doc_data in document_texts:
            try:
                if doc_data['text']:
                    doc_type, confidence = await self.classifier.classify_document(
                        doc_data['text'], doc_data['filename']
                    )
                else:
                    doc_type, confidence = DocumentType.UNKNOWN, 0.0
                
                classified_docs.append({
                    **doc_data,
                    'document_type': doc_type,
                    'classification_confidence': confidence
                })
                
            except Exception as e:
                logger.error(f"Error classifying {doc_data['filename']}: {str(e)}")
                classified_docs.append({
                    **doc_data,
                    'document_type': DocumentType.UNKNOWN,
                    'classification_confidence': 0.0,
                    'classification_error': str(e)
                })
        
        return classified_docs
    
    async def _process_with_agents(self, classified_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process documents with specialized agents"""
        processed_docs = []
        
        # Process documents concurrently
        tasks = []
        for doc_data in classified_docs:
            task = self._process_single_document(doc_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent processing error: {str(result)}")
                processed_docs.append({
                    'filename': 'unknown',
                    'document_type': DocumentType.UNKNOWN,
                    'agent_response': None,
                    'error': str(result)
                })
            else:
                processed_docs.append(result)
        
        return processed_docs
    
    async def _process_single_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process single document with appropriate agent"""
        try:
            doc_type = doc_data['document_type']
            
            if doc_type in self.agents and doc_data['text']:
                agent = self.agents[doc_type]
                agent_response = await agent.process_document(
                    doc_data['text'], doc_data['filename']
                )
                
                return {
                    **doc_data,
                    'agent_response': agent_response
                }
            else:
                logger.warning(f"No agent available for document type: {doc_type}")
                return {
                    **doc_data,
                    'agent_response': None
                }
                
        except Exception as e:
            logger.error(f"Error processing document {doc_data['filename']}: {str(e)}")
            return {
                **doc_data,
                'agent_response': None,
                'processing_error': str(e)
            }
    
    async def _validate_claim_data(self, processed_docs: List[Dict[str, Any]]) -> ValidationResult:
        """Validate processed claim data"""
        return await self.validator.validate_claim(processed_docs)
    
    async def _make_claim_decision(self, processed_docs: List[Dict[str, Any]], 
                                  validation_result: ValidationResult) -> ClaimDecision:
        """Make final claim decision based on processed data and validation"""
        try:
            # Check for required documents first
            doc_types = [doc.get('document_type') for doc in processed_docs]
            has_bill = DocumentType.BILL in doc_types
            
            if not has_bill:
                return ClaimDecision(
                    status=ClaimStatus.REJECTED,
                    reason="Missing required medical bill document",
                    confidence=0.9
                )
            
            # If we have discrepancies, check if they're insurance-related (should reject)
            if validation_result.discrepancies:
                # Check if discrepancies are related to insurance claims
                insurance_related = any(
                    'insurance' in disc.lower() for disc in validation_result.discrepancies
                )
                
                if insurance_related:
                    return ClaimDecision(
                        status=ClaimStatus.REJECTED,
                        reason=f"Insurance claim validation failed: {', '.join(validation_result.discrepancies)}",
                        confidence=0.3
                    )
                else:
                    # Non-insurance discrepancies can be approved with warnings
                    return ClaimDecision(
                        status=ClaimStatus.APPROVED,
                        reason=f"Approved with warnings: {', '.join(validation_result.discrepancies)}",
                        confidence=0.7
                    )
            
            # Check data quality and confidence
            total_confidence = 0
            valid_docs = 0
            
            for doc in processed_docs:
                if doc.get('agent_response') and doc['agent_response'].confidence > 0.3:
                    total_confidence += doc['agent_response'].confidence
                    valid_docs += 1
            
            avg_confidence = total_confidence / valid_docs if valid_docs > 0 else 0
            
            # Stricter confidence threshold for insurance claims
            if avg_confidence < 0.7:
                return ClaimDecision(
                    status=ClaimStatus.REQUIRES_REVIEW,
                    reason="Low confidence in extracted data. Manual review required.",
                    confidence=avg_confidence
                )
            
            # Approve if all checks pass, even with warnings
            reason = "All required documents present and data is consistent"
            if validation_result.warnings:
                reason = f"Approved with minor warnings: {', '.join(validation_result.warnings)}"
            
            return ClaimDecision(
                status=ClaimStatus.APPROVED,
                reason=reason,
                confidence=avg_confidence
            )
            
        except Exception as e:
            logger.error(f"Error making claim decision: {str(e)}")
            return ClaimDecision(
                status=ClaimStatus.REJECTED,
                reason=f"Decision processing error: {str(e)}",
                confidence=0.0
            )
    
    def _create_documents_info(self, processed_docs: List[Dict[str, Any]]) -> List[DocumentInfo]:
        """Create document info list for response"""
        documents_info = []
        
        for doc in processed_docs:
            extracted_data = {}
            confidence = 0.0
            
            if doc.get('agent_response'):
                extracted_data = doc['agent_response'].extracted_data
                confidence = doc['agent_response'].confidence
            
            documents_info.append(DocumentInfo(
                type=doc.get('document_type', DocumentType.UNKNOWN),
                filename=doc.get('filename', 'unknown'),
                confidence=confidence,
                extracted_data=extracted_data
            ))
        
        return documents_info
    
    def _create_structured_data(self, processed_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create structured data summary"""
        structured_data = {
            'documents': [],
            'summary': {
                'total_documents': len(processed_docs),
                'processed_successfully': 0,
                'processing_errors': 0
            }
        }
        
        for doc in processed_docs:
            if doc.get('agent_response'):
                structured_data['documents'].append({
                    'type': doc['document_type'].value,
                    'filename': doc['filename'],
                    'data': doc['agent_response'].extracted_data
                })
                structured_data['summary']['processed_successfully'] += 1
            else:
                structured_data['summary']['processing_errors'] += 1
        
        return structured_data
