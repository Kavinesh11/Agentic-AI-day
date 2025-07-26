"""Configuration settings for Personal Finance Assistant"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    # Google Cloud settings
    google_api_key: Optional[str] = None
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"
    google_application_credentials: Optional[str] = None
    google_genai_use_vertexai: bool = False

    # Google Wallet settings
    wallet_issuer_id: Optional[str] = None
    wallet_service_account_file: Optional[str] = None

    # ADK settings
    adk_model: str = "gemini-2.0-flash"
    adk_app_name: str = "PersonalFinanceAssistant"

    # MCP settings
    mcp_server_timeout: int = 30
    mcp_max_retries: int = 3

    # Financial analysis settings
    default_currency: str = "USD"
    risk_threshold: float = 0.8
    emergency_fund_months: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
