import asyncio
import logging
import os
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models.schemas import ClaimProcessingResponse
from services.claim_processor import ClaimProcessor
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medical Insurance Claim Processor",
    description="AI-powered backend for processing medical insurance claims",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize claim processor
claim_processor = ClaimProcessor()

@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "Medical Insurance Claim Processor API", "status": "healthy"}

@app.post("/process-claim", response_model=ClaimProcessingResponse)
async def process_claim(files: List[UploadFile] = File(...)):
    """
    Process medical insurance claim documents
    
    Args:
        files: List of PDF files (bill, ID card, discharge summary, etc.)
        
    Returns:
        ClaimProcessingResponse: Structured claim processing result
    """
    try:
        logger.info(f"Processing claim with {len(files)} files")
        
        # Validate file types
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only PDF files are supported."
                )
        
        # Process the claim
        result = await claim_processor.process_claim_documents(files)
        
        logger.info("Claim processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing claim: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing claim: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    try:
        # Check if Gemini API is accessible
        from services.text_extractor import TextExtractor
        extractor = TextExtractor()
        
        return {
            "status": "healthy",
            "services": {
                "gemini_api": "available",
                "claim_processor": "ready"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
