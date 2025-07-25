from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_TITLE: str = "Receipt Processor API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]

    # Agent Configuration
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    # A2A Configuration
    RETAIL_PARSER_URL: str = "http://localhost:8001"
    FOOD_PARSER_URL: str = "http://localhost:8002"
    MISC_PARSER_URL: str = "http://localhost:8003"

    # Firebase Configuration (for future use)
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
