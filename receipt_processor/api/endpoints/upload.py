
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import mimetypes

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...agents.agent import receipt_processor_system

logger = logging.getLogger(__name__)

# Pydantic models for request/response


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_status: str
    processed_at: str
    workflow_id: Optional[str] = None
    processing_result: Optional[Dict[str, Any]] = None


class BulkUploadResponse(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    upload_results: List[UploadResponse]
    errors: List[Dict[str, Any]]


# Create router
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/single", response_model=UploadResponse)
async def upload_single_receipt(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    process_immediately: bool = Form(True),
    input_mode: str = Form("manual")
) -> UploadResponse:
    """Upload a single receipt file with optional immediate processing."""

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG, PNG, WebP)"
            )

        # Validate file size (10MB limit)
        file_data = await file.read()
        if len(file_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 10MB limit"
            )

        upload_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        upload_response = UploadResponse(
            upload_id=upload_id,
            filename=file.filename or "receipt.jpg",
            file_size=len(file_data),
            mime_type=file.content_type,
            upload_status="uploaded",
            processed_at=datetime.now().isoformat()
        )

        # Process immediately if requested
        if process_immediately:
            try:
                processing_result = await receipt_processor_system.handle_receipt_upload(
                    file_data=file_data,
                    filename=file.filename or "receipt.jpg",
                    user_id=user_id,
                    upload_mode=input_mode
                )

                upload_response.workflow_id = processing_result.get(
                    "workflow_id")
                upload_response.processing_result = processing_result
                upload_response.upload_status = "processed"

            except Exception as e:
                logger.error(f"Processing failed for upload {upload_id}: {e}")
                upload_response.upload_status = "upload_success_processing_failed"
                upload_response.processing_result = {"error": str(e)}

        return upload_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=BulkUploadResponse)
async def upload_bulk_receipts(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    process_immediately: bool = Form(True),
    input_mode: str = Form("manual")
) -> BulkUploadResponse:
    """Upload multiple receipt files with batch processing."""

    try:
        if len(files) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 files allowed per bulk upload"
            )

        upload_results = []
        errors = []
        successful_count = 0

        for i, file in enumerate(files):
            try:
                # Validate each file
                if not file.content_type or not file.content_type.startswith('image/'):
                    errors.append({
                        "index": i,
                        "filename": file.filename,
                        "error": "File must be an image"
                    })
                    continue

                file_data = await file.read()
                if len(file_data) > 10 * 1024 * 1024:
                    errors.append({
                        "index": i,
                        "filename": file.filename,
                        "error": "File size exceeds 10MB limit"
                    })
                    continue

                upload_id = f"bulk_upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{i}"

                upload_result = UploadResponse(
                    upload_id=upload_id,
                    filename=file.filename or f"receipt_{i}.jpg",
                    file_size=len(file_data),
                    mime_type=file.content_type,
                    upload_status="uploaded",
                    processed_at=datetime.now().isoformat()
                )

                # Process if requested
                if process_immediately:
                    try:
                        processing_result = await receipt_processor_system.handle_receipt_upload(
                            file_data=file_data,
                            filename=file.filename or f"receipt_{i}.jpg",
                            user_id=user_id,
                            upload_mode=input_mode
                        )

                        upload_result.workflow_id = processing_result.get(
                            "workflow_id")
                        upload_result.processing_result = processing_result
                        upload_result.upload_status = "processed"

                    except Exception as e:
                        logger.error(
                            f"Processing failed for bulk upload {upload_id}: {e}")
                        upload_result.upload_status = "upload_success_processing_failed"
                        upload_result.processing_result = {"error": str(e)}

                upload_results.append(upload_result)
                successful_count += 1

            except Exception as e:
                errors.append({
                    "index": i,
                    "filename": file.filename,
                    "error": str(e)
                })

        return BulkUploadResponse(
            total_files=len(files),
            successful_uploads=successful_count,
            failed_uploads=len(errors),
            upload_results=upload_results,
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url")
async def upload_from_url(
    image_url: str = Form(...),
    user_id: str = Form(...),
    process_immediately: bool = Form(True),
    input_mode: str = Form("url")
) -> UploadResponse:
    """Upload receipt from URL."""

    try:
        import httpx

        # Download image from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, timeout=30.0)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail="URL does not point to a valid image"
                )

            file_data = response.content
            if len(file_data) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="Image size exceeds 10MB limit"
                )

        # Extract filename from URL
        filename = image_url.split('/')[-1] or "receipt_from_url.jpg"
        upload_id = f"url_upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        upload_response = UploadResponse(
            upload_id=upload_id,
            filename=filename,
            file_size=len(file_data),
            mime_type=content_type,
            upload_status="uploaded",
            processed_at=datetime.now().isoformat()
        )

        # Process if requested
        if process_immediately:
            try:
                processing_result = await receipt_processor_system.handle_receipt_upload(
                    file_data=file_data,
                    filename=filename,
                    user_id=user_id,
                    upload_mode=input_mode
                )

                upload_response.workflow_id = processing_result.get(
                    "workflow_id")
                upload_response.processing_result = processing_result
                upload_response.upload_status = "processed"

            except Exception as e:
                logger.error(
                    f"Processing failed for URL upload {upload_id}: {e}")
                upload_response.upload_status = "upload_success_processing_failed"
                upload_response.processing_result = {"error": str(e)}

        return upload_response

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to download image: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get supported file formats and upload limits."""

    return {
        "supported_formats": [
            "image/jpeg",
            "image/png",
            "image/webp"
        ],
        "max_file_size": "10MB",
        "max_bulk_files": 20,
        "input_modes": [
            "manual",
            "camera",
            "screenshot",
            "email",
            "url"
        ]
    }


@router.get("/status/{upload_id}")
async def get_upload_status(upload_id: str) -> Dict[str, Any]:
    """Get the status of a specific upload."""

    try:
        # This would typically query the database for upload status
        # TODO: Implement upload tracking in Firebase

        return {
            "upload_id": upload_id,
            "status": "unknown",
            "message": "Upload tracking not yet implemented"
        }

    except Exception as e:
        logger.error(f"Error getting upload status {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
