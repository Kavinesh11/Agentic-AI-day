"""Configuration module for receipt processing system."""

from .firebase_config import FirebaseConfig
from .settings import Settings

__all__ = [
    'FirebaseConfig',
    'Settings',
]
