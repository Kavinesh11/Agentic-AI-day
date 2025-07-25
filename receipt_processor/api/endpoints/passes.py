import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...agents.pass_generator_agent import pass_generator_agent
from ...agents.agent import receipt_processor_system

logger = logging.getLogger(__name__)

# Pydantic models for request/response


class PassGenerationRequest(BaseModel):
    receipt_data: Dict[str, Any]
    user_id: str
    pass_type: Optional[str] = None


class PassResponse(BaseModel):
    pass_id: str
    pass_type: str
    merchant_name: str
    amount: float
    date: str
    description: str
    metadata: Dict[str, Any]
    created_at: str


class PassListResponse(BaseModel):
    passes: List[PassResponse]
    total_count: int
    user_id: str


class PassInsightsResponse(BaseModel):
    user_id: str
    total_passes: int
    categories: Dict[str, int]
    spending_summary: Dict[str, float]
    insights: List[str]


# Create router
router = APIRouter(prefix="/passes", tags=["passes"])


@router.post("/generate", response_model=PassResponse)
async def generate_pass(request: PassGenerationRequest) -> PassResponse:
    """Generate a wallet pass from parsed receipt data."""

    try:
        # Use the pass generator agent to create the pass
        pass_result = await pass_generator_agent.agent.run_async(
            user_message="Generate wallet pass from parsed receipt",
            receipt_data=request.receipt_data
        )

        if not pass_result or "error" in pass_result:
            raise HTTPException(
                status_code=400,
                detail="Failed to generate wallet pass"
            )

        # Extract pass data from agent response
        pass_data = pass_result.get("passData", {})

        return PassResponse(
            pass_id=pass_data.get("passId", ""),
            pass_type=pass_data.get("passType", "generic"),
            merchant_name=pass_data.get("merchantName", ""),
            amount=pass_data.get("amount", 0.0),
            date=pass_data.get("date", ""),
            description=pass_data.get("description", ""),
            metadata=pass_result.get("metadata", {}),
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error generating pass: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pass_id}", response_model=PassResponse)
async def get_pass(pass_id: str) -> PassResponse:
    """Retrieve a specific wallet pass by ID."""

    try:
        # This would typically query Firebase/database
        # For now, return a placeholder response
        # TODO: Implement Firebase integration

        raise HTTPException(
            status_code=404,
            detail=f"Pass {pass_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pass {pass_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=PassListResponse)
async def list_user_passes(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None
) -> PassListResponse:
    """List all passes for a specific user."""

    try:
        # This would typically query Firebase/database
        # For now, return empty list
        # TODO: Implement Firebase integration

        return PassListResponse(
            passes=[],
            total_count=0,
            user_id=user_id
        )

    except Exception as e:
        logger.error(f"Error listing passes for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pass_id}")
async def delete_pass(pass_id: str) -> Dict[str, str]:
    """Delete a wallet pass."""

    try:
        # This would typically delete from Firebase/database
        # TODO: Implement Firebase integration

        return {"message": f"Pass {pass_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting pass {pass_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{pass_id}", response_model=PassResponse)
async def update_pass(
    pass_id: str,
    updates: Dict[str, Any]
) -> PassResponse:
    """Update a wallet pass."""

    try:
        # This would typically update Firebase/database
        # TODO: Implement Firebase integration

        raise HTTPException(
            status_code=404,
            detail=f"Pass {pass_id} not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pass {pass_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/insights", response_model=PassInsightsResponse)
async def get_user_insights(user_id: str) -> PassInsightsResponse:
    """Get spending insights and analytics for a user."""

    try:
        # Use the root agent to generate spending report
        report = await receipt_processor_system.agent.run_async(
            user_message=f"Generate spending report for user {user_id}",
            user_id=user_id
        )

        return PassInsightsResponse(
            user_id=user_id,
            total_passes=0,
            categories={},
            spending_summary={},
            insights=[]
        )

    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-generate")
async def bulk_generate_passes(
    receipt_data_list: List[Dict[str, Any]],
    user_id: str
) -> Dict[str, Any]:
    """Generate multiple passes from a batch of receipt data."""

    try:
        results = []
        errors = []

        for i, receipt_data in enumerate(receipt_data_list):
            try:
                request = PassGenerationRequest(
                    receipt_data=receipt_data,
                    user_id=user_id
                )
                pass_result = await generate_pass(request)
                results.append(pass_result)
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e)
                })

        return {
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Error in bulk pass generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
async def list_pass_categories() -> Dict[str, List[str]]:
    """Get available pass categories and types."""

    return {
        "categories": [
            "Food & Dining",
            "Shopping",
            "Transportation",
            "Healthcare",
            "Entertainment",
            "Utilities",
            "Miscellaneous"
        ],
        "pass_types": [
            "retail",
            "dining",
            "utility",
            "generic"
        ]
    }
