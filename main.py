"""
Receipt Management System - FastAPI Application

This application provides a receipt management system using multi-agent architecture
with Gemini 2.0 Flash for receipt classification and parsing.
"""

import os
import json
import base64
import uuid
from typing import Dict, Any
from io import BytesIO
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn
from dotenv import load_dotenv

# ADK imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from receipt_agent import root_agent

# Load environment variables
load_dotenv()

# Initialize ADK components
session_service = InMemorySessionService()
APP_NAME = "Receipt Management System"
USER_ID = "api_user"

# Create runner with the root agent
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

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
        JSON response with bill ID and structured receipt data
    """
    try:
        # Validate file type - check both content_type and file extension
        file_extension = os.path.splitext(file.filename or "")[1].lower()
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Check content type if available
        content_type_valid = (
            file.content_type and 
            file.content_type.startswith('image/')
        )
        
        # Check file extension
        extension_valid = file_extension in valid_extensions
        
        if not (content_type_valid or extension_valid):
            raise HTTPException(
                status_code=400, 
                detail=f"File must be an image. Received content-type: {file.content_type}, extension: {file_extension}"
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
        
        # Create prompt for multi-agent system
        prompt = f"""
        Please process this receipt image. The image is provided as base64 data.
        
        Image data: data:image/jpeg;base64,{image_base64}
        
        Analyze and extract information from this receipt.
        """
        
        # Create a new session for this request
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state={}
        )
        session_id = session.id
        
        # Create content for the agent
        content = types.Content(
            role="user", 
            parts=[types.Part(text=prompt)]
        )
        
        # Run the multi-agent system
        final_response = None
        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=content
            ):
                # Get the final response from the last event
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response = part.text
                elif hasattr(event, 'text'):
                    final_response = event.text
        except Exception as e:
            raise Exception(f"Agent processing failed: {str(e)}")
        
        if not final_response:
            raise Exception("No response received from agent")
        
        # Try to parse as JSON
        try:
            # Clean up the response if it has markdown formatting
            response_text = final_response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            parsed_result = json.loads(response_text)
                
            # Ensure we have the required fields and generate UUID if missing
            if isinstance(parsed_result, dict):
                if 'billId' not in parsed_result:
                    parsed_result['billId'] = str(uuid.uuid4())
                if 'uploadDate' not in parsed_result:
                    parsed_result['uploadDate'] = datetime.now().isoformat() + 'Z'
                if 'uploaderId' not in parsed_result:
                    parsed_result['uploaderId'] = "user123"
                if 'imageUrl' not in parsed_result:
                    parsed_result['imageUrl'] = f"https://firebasestorage.googleapis.com/{parsed_result.get('billId', 'unknown')}.jpg"
                
                return JSONResponse(content=parsed_result)
            else:
                # Fallback structure if parsing fails
                return JSONResponse(content={
                    "billId": str(uuid.uuid4()),
                    "billType": "Unknown",
                    "uploadDate": datetime.now().isoformat() + 'Z',
                    "uploaderId": "user123",
                    "imageUrl": "https://firebasestorage.googleapis.com/unknown.jpg",
                    "parsedData": {
                        "error": "Failed to parse receipt data",
                        "raw_response": str(final_response)
                    }
                })
                
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return error structure
            return JSONResponse(content={
                "billId": str(uuid.uuid4()),
                "billType": "Error",
                "uploadDate": datetime.now().isoformat() + 'Z',
                "uploaderId": "user123",
                "imageUrl": "https://firebasestorage.googleapis.com/error.jpg",
                "parsedData": {
                    "error": f"JSON parsing failed: {str(e)}",
                    "raw_response": str(final_response)
                }
            })
        
    except HTTPException:
        raise
    except Exception as e:
        # Return error in the expected format
        return JSONResponse(
            status_code=500,
            content={
                "billId": str(uuid.uuid4()),
                "billType": "Error",
                "uploadDate": datetime.now().isoformat() + 'Z',
                "uploaderId": "user123",
                "imageUrl": "https://firebasestorage.googleapis.com/error.jpg",
                "parsedData": {
                    "error": f"Processing failed: {str(e)}",
                    "filename": file.filename,
                    "file_size": len(image_data) if 'image_data' in locals() else 0
                }
            }
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