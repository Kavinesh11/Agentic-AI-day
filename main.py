"""
Receipt Management System - FastAPI Application

This application provides a receipt management system using multi-agent architecture
with Gemini 2.0 Flash for receipt classification and parsing.
"""

import os
import json
import base64
from typing import Dict, Any
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn
from dotenv import load_dotenv

from receipt_agent import root_agent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Receipt Management System",
    description="A multi-agent receipt processing system using Gemini 2.0 Flash",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Receipt Management System API",
        "version": "1.0.0",
        "endpoints": {
            "/process-receipt": "POST - Upload and process receipt image",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "receipt-management-system"}

@app.post("/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """
    Process uploaded receipt image through multi-agent system.
    
    Args:
        file: Uploaded image file (JPEG, PNG)
        
    Returns:
        JSON response with receipt classification and extracted data
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read and validate image
        image_data = await file.read()
        try:
            image = Image.open(BytesIO(image_data))
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Convert image to base64 for processing
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Process through multi-agent system
        prompt = f"""
        Please process this receipt image. The image is provided as base64 data.
        
        Image data: data:image/jpeg;base64,{image_base64}
        
        Analyze and extract information from this receipt.
        """
        
        # Run the multi-agent system
        result = root_agent.run(prompt)
        
        # Parse the result
        if hasattr(result, 'content'):
            response_content = result.content
        else:
            response_content = str(result)
        
        return JSONResponse(
            content={
                "status": "success",
                "filename": file.filename,
                "file_size": len(image_data),
                "processing_result": response_content
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing receipt: {str(e)}"
        )

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    ) 