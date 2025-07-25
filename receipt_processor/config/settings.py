"""
Application Settings

Configuration settings for the receipt processor application.
"""

from pydantic import BaseSettings, Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = Field(default="Receipt Processor", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Security settings
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    valid_api_keys: List[str] = Field(default=[], env="VALID_API_KEYS")

    # Database settings
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    # Firebase settings
    firebase_credentials_path: Optional[str] = Field(
        default=None, env="FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: Optional[str] = Field(
        default=None, env="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: Optional[str] = Field(
        default=None, env="FIREBASE_STORAGE_BUCKET")

    # OCR settings
    ocr_service: str = Field(default="tesseract", env="OCR_SERVICE")
    google_vision_api_key: Optional[str] = Field(
        default=None, env="GOOGLE_VISION_API_KEY")
    aws_access_key_id: Optional[str] = Field(
        default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")

    # File upload settings
    max_file_size: int = Field(
        default=10485760, env="MAX_FILE_SIZE")  # 10MB in bytes
    allowed_file_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/bmp",
                 "image/tiff", "application/pdf"],
        env="ALLOWED_FILE_TYPES"
    )
    upload_directory: str = Field(default="uploads", env="UPLOAD_DIRECTORY")

    # Pass generation settings
    apple_wallet_team_id: Optional[str] = Field(
        default=None, env="APPLE_WALLET_TEAM_ID")
    apple_wallet_pass_type_id: Optional[str] = Field(
        default=None, env="APPLE_WALLET_PASS_TYPE_ID")
    apple_wallet_certificate_path: Optional[str] = Field(
        default=None, env="APPLE_WALLET_CERTIFICATE_PATH")
    apple_wallet_private_key_path: Optional[str] = Field(
        default=None, env="APPLE_WALLET_PRIVATE_KEY_PATH")
    google_pay_issuer_id: Optional[str] = Field(
        default=None, env="GOOGLE_PAY_ISSUER_ID")
    google_pay_service_account_path: Optional[str] = Field(
        default=None, env="GOOGLE_PAY_SERVICE_ACCOUNT_PATH")

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")

    # Redis settings (for caching)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour in seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the application settings.

    Returns:
        Settings instance
    """
    return settings

# Environment-specific configurations


class DevelopmentSettings(Settings):
    """Development environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""
    debug: bool = False
    log_level: str = "WARNING"
    cors_origins: List[str] = []  # Should be restricted in production


class TestingSettings(Settings):
    """Testing environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///test.db"


def get_environment_settings() -> Settings:
    """
    Get settings based on the current environment.

    Returns:
        Environment-specific settings
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()
