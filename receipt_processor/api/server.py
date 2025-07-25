"""
API Server

Main FastAPI server for the receipt processing system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import upload, receipts, passes

app = FastAPI(
    title="Receipt Processor API",
    description="API for processing receipts and generating mobile wallet passes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(
    receipts.router, prefix="/api/v1/receipts", tags=["receipts"])
app.include_router(passes.router, prefix="/api/v1/passes", tags=["passes"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Receipt Processor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
