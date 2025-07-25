import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ...agent import receipt_processor_system
from ...agents.input_handler_agent import input_handler_agent

logger = logging.getLogger(__name__)

# Pydantic models for request/response


class ReceiptUploadRequest(BaseModel):
    user_id: str
    input_mode: str = "manual"  # camera, screenshot, email, manual
    category_hint: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None


class ReceiptProcessingResponse(BaseModel):
    workflow_id: str
    status: str
    classification: Optional[Dict[str, Any]] = None
    parsed_data: Optional[Dict[str, Any]] = None
    wallet_pass: Optional[Dict[str, Any]] = None
    processed_at: str
    error: Optional[str] = None


class ReceiptListResponse(BaseModel):
    receipts: List[Dict[str, Any]]
    total_count: int
    user_id: str


class ReceiptClassificationResponse(BaseModel):
    category: str
    confidence: float
    detected_features: List[str]
    routing_agent: str
    processed_at: str


# Create router
router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/upload", response_model=ReceiptProcessingResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    input_mode: str = Form("manual"),
    category_hint: Optional[str] = Form(None)
) -> ReceiptProcessingResponse:
    """Upload and process a receipt image through the complete workflow."""

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Read file data
        file_data = await file.read()

        # Process through the complete workflow
        result = await receipt_processor_system.handle_receipt_upload(
            file_data=file_data,
            filename=file.filename or "receipt.jpg",
            user_id=user_id,
            upload_mode=input_mode
        )

        return ReceiptProcessingResponse(
            workflow_id=result.get("workflow_id", ""),
            status=result.get("status", "failed"),
            classification=result.get("classification"),
            parsed_data=result.get("parsed_data"),
            wallet_pass=result.get("wallet_pass"),
            processed_at=result.get(
                "processed_at", datetime.now().isoformat()),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error uploading receipt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=ReceiptClassificationResponse)
async def classify_receipt(
    file: UploadFile = File(...),
    user_context: Optional[str] = Form(None)
) -> ReceiptClassificationResponse:
    """Classify a receipt image without full processing."""

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Read file data
        file_data = await file.read()

        # Use input handler agent for classification only
        classification_result = await input_handler_agent.classify_receipt(
            image_data=file_data,
            mime_type=file.content_type,
            user_context=user_context
        )

        return ReceiptClassificationResponse(
            category=classification_result.get("category", "unknown"),
            confidence=classification_result.get("confidence", 0.0),
            detected_features=classification_result.get(
                "detected_features", []),
            routing_agent=classification_result.get(
                "routing_agent", "misc_parser_agent"),
            processed_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error classifying receipt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{receipt_id}")
async def get_receipt(receipt_id: str) -> Dict[str, Any]:
    """Retrieve a specific receipt by ID."""

    try:
        # This would typically query Firebase/database
        # TODO: Implement Firebase integration

        raise HTTPException(
            status_code=404,
            detail=f"Receipt {receipt_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving receipt {receipt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=ReceiptListResponse)
async def list_user_receipts(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> ReceiptListResponse:
    """List all receipts for a specific user with filtering options."""

    try:
        # This would typically query Firebase/database
        # TODO: Implement Firebase integration

        return ReceiptListResponse(
            receipts=[],
            total_count=0,
            user_id=user_id
        )

    except Exception as e:
        logger.error(f"Error listing receipts for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{receipt_id}")
async def delete_receipt(receipt_id: str) -> Dict[str, str]:
    """Delete a receipt and associated data."""

    try:
        # This would typically delete from Firebase/database
        # TODO: Implement Firebase integration

        return {"message": f"Receipt {receipt_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting receipt {receipt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{receipt_id}")
async def update_receipt(
    receipt_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Update receipt metadata or reprocess."""

    try:
        # This would typically update Firebase/database
        # TODO: Implement Firebase integration

        raise HTTPException(
            status_code=404,
            detail=f"Receipt {receipt_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating receipt {receipt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess/{receipt_id}")
async def reprocess_receipt(receipt_id: str) -> ReceiptProcessingResponse:
    """Reprocess an existing receipt through the workflow."""

    try:
        # This would fetch the original receipt data and reprocess
        # TODO: Implement Firebase integration

        raise HTTPException(
            status_code=404,
            detail=f"Receipt {receipt_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing receipt {receipt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-upload")
async def batch_upload_receipts(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    input_mode: str = Form("manual")
) -> Dict[str, Any]:
    """Upload and process multiple receipts in batch."""

    try:
        results = []
        errors = []

        for i, file in enumerate(files):
            try:
                # Validate file type
                if not file.content_type or not file.content_type.startswith('image/'):
                    errors.append({
                        "index": i,
                        "filename": file.filename,
                        "error": "File must be an image"
                    })
                    continue

                # Process each file
                file_data = await file.read()
                result = await receipt_processor_system.handle_receipt_upload(
                    file_data=file_data,
                    filename=file.filename or f"receipt_{i}.jpg",
                    user_id=user_id,
                    upload_mode=input_mode
                )
                results.append(result)

            except Exception as e:
                errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": str(e)
                })

        return {
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/supported")
async def get_supported_categories() -> Dict[str, List[str]]:
    """Get supported receipt categories and input modes."""

    return {
        "categories": [
            "retail",
            "food_dining",
            "miscellaneous"
        ],
        "input_modes": [
            "camera",
            "screenshot",
            "email",
            "manual"
        ],
        "supported_formats": [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]
    }


@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get the status of a receipt processing workflow."""

    try:
        # This would typically query workflow status from database
        # TODO: Implement workflow tracking

        return {
            "workflow_id": workflow_id,
            "status": "unknown",
            "message": "Workflow tracking not yet implemented"
        }

    except Exception as e:
        logger.error(f"Error getting workflow status {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
