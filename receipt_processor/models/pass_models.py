"""
Pass Data Models

Pydantic models for mobile wallet pass data validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PassType(str, Enum):
    """Enumeration of pass types."""
    APPLE_WALLET = "apple_wallet"
    GOOGLE_PAY = "google_pay"


class PassStatus(str, Enum):
    """Enumeration of pass statuses."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PassField(BaseModel):
    """Model for pass fields (primary, secondary, auxiliary, back)."""
    key: str = Field(..., description="Field key")
    label: str = Field(..., description="Field label")
    value: str = Field(..., description="Field value")
    textAlignment: Optional[str] = Field(None, description="Text alignment")


class PassLocation(BaseModel):
    """Model for pass location data."""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude")
    relevantText: Optional[str] = Field(
        None, description="Text to display when near location")


class PassBarcode(BaseModel):
    """Model for pass barcode/QR code data."""
    format: str = Field(...,
                        description="Barcode format (QR, PDF417, Aztec, Code128)")
    message: str = Field(..., description="Barcode message/data")
    messageEncoding: str = Field(
        default="iso-8859-1", description="Message encoding")
    altText: Optional[str] = Field(None, description="Alternative text")


class AppleWalletPass(BaseModel):
    """Model for Apple Wallet pass data."""
    formatVersion: int = Field(default=1, description="Pass format version")
    passTypeIdentifier: str = Field(..., description="Pass type identifier")
    serialNumber: str = Field(..., description="Serial number")
    teamIdentifier: str = Field(..., description="Team identifier")
    organizationName: str = Field(..., description="Organization name")
    description: str = Field(..., description="Pass description")
    logoText: Optional[str] = Field(None, description="Logo text")
    foregroundColor: Optional[str] = Field(
        None, description="Foreground color")
    backgroundColor: Optional[str] = Field(
        None, description="Background color")
    labelColor: Optional[str] = Field(None, description="Label color")
    barcode: Optional[PassBarcode] = Field(None, description="Barcode data")
    locations: Optional[List[PassLocation]] = Field(
        None, description="Relevant locations")
    primaryFields: Optional[List[PassField]] = Field(
        None, description="Primary fields")
    secondaryFields: Optional[List[PassField]] = Field(
        None, description="Secondary fields")
    auxiliaryFields: Optional[List[PassField]] = Field(
        None, description="Auxiliary fields")
    backFields: Optional[List[PassField]] = Field(
        None, description="Back fields")


class GooglePayPass(BaseModel):
    """Model for Google Pay pass data."""
    iss: str = Field(..., description="Issuer identifier")
    aud: str = Field(default="google", description="Audience")
    typ: str = Field(default="savetowallet", description="Token type")
    origins: List[str] = Field(..., description="Allowed origins")
    payload: Dict[str, Any] = Field(..., description="Pass payload data")


class Pass(BaseModel):
    """Main pass data model."""
    id: Optional[str] = Field(None, description="Unique pass identifier")
    receipt_id: str = Field(..., description="Associated receipt ID")
    type: PassType = Field(..., description="Type of pass")
    status: PassStatus = Field(
        default=PassStatus.ACTIVE, description="Pass status")
    template_id: Optional[str] = Field(
        None, description="Template used for generation")
    apple_wallet_data: Optional[AppleWalletPass] = Field(
        None, description="Apple Wallet specific data")
    google_pay_data: Optional[GooglePayPass] = Field(
        None, description="Google Pay specific data")
    file_url: Optional[str] = Field(None, description="URL to pass file")
    download_count: int = Field(default=0, description="Number of downloads")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Last update timestamp")
    expires_at: Optional[datetime] = Field(
        None, description="Pass expiration date")


class PassCreateRequest(BaseModel):
    """Model for pass creation requests."""
    receipt_id: str = Field(..., description="Receipt ID to generate pass for")
    type: PassType = Field(..., description="Type of pass to generate")
    template_id: Optional[str] = Field(None, description="Template to use")
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Custom field overrides")
    expires_at: Optional[datetime] = Field(
        None, description="Pass expiration date")


class PassUpdateRequest(BaseModel):
    """Model for pass update requests."""
    status: Optional[PassStatus] = Field(
        None, description="Updated pass status")
    expires_at: Optional[datetime] = Field(
        None, description="Updated expiration date")
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Updated custom fields")
