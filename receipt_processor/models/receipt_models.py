"""
Receipt Data Models

Pydantic models for receipt data validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReceiptType(str, Enum):
    """Enumeration of receipt types."""
    RETAIL = "retail"
    FOOD = "food"
    MISC = "misc"


class ReceiptItem(BaseModel):
    """Model for individual receipt items."""
    name: str = Field(..., description="Item name")
    quantity: Optional[float] = Field(None, description="Item quantity")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    total_price: float = Field(..., description="Total price for this item")
    category: Optional[str] = Field(None, description="Item category")


class VendorInfo(BaseModel):
    """Model for vendor/merchant information."""
    name: str = Field(..., description="Vendor name")
    address: Optional[str] = Field(None, description="Vendor address")
    phone: Optional[str] = Field(None, description="Vendor phone number")
    email: Optional[str] = Field(None, description="Vendor email")
    website: Optional[str] = Field(None, description="Vendor website")


class ReceiptTotals(BaseModel):
    """Model for receipt totals and financial information."""
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    tax: Optional[float] = Field(None, description="Tax amount")
    tip: Optional[float] = Field(None, description="Tip amount")
    discount: Optional[float] = Field(None, description="Discount amount")
    total: float = Field(..., description="Final total amount")


class Receipt(BaseModel):
    """Main receipt data model."""
    id: Optional[str] = Field(None, description="Unique receipt identifier")
    type: ReceiptType = Field(..., description="Type of receipt")
    vendor: VendorInfo = Field(..., description="Vendor information")
    date: datetime = Field(..., description="Receipt date and time")
    items: List[ReceiptItem] = Field(
        default_factory=list, description="List of items")
    totals: ReceiptTotals = Field(..., description="Receipt totals")
    currency: str = Field(default="USD", description="Currency code")
    payment_method: Optional[str] = Field(
        None, description="Payment method used")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    raw_text: Optional[str] = Field(None, description="Raw OCR text")
    image_url: Optional[str] = Field(None, description="URL to receipt image")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Last update timestamp")


class ReceiptCreateRequest(BaseModel):
    """Model for receipt creation requests."""
    type: Optional[ReceiptType] = Field(
        None, description="Suggested receipt type")
    file_data: Optional[str] = Field(
        None, description="Base64 encoded file data")
    file_url: Optional[str] = Field(None, description="URL to receipt file")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata")


class ReceiptUpdateRequest(BaseModel):
    """Model for receipt update requests."""
    vendor: Optional[VendorInfo] = Field(
        None, description="Updated vendor information")
    items: Optional[List[ReceiptItem]] = Field(
        None, description="Updated items list")
    totals: Optional[ReceiptTotals] = Field(None, description="Updated totals")
    payment_method: Optional[str] = Field(
        None, description="Updated payment method")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Updated metadata")
