"""
Configuration management for Eva backend.
Handles environment variables and application settings using Pydantic.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    These settings configure:
    - Google Cloud integration (Keys and Project)
    - OAuth authentication
    - API server configuration
    """
    
    # Google Cloud Configuration
    google_cloud_project: str = "eva-backend-service"
    google_application_credentials: str = "service-account-key.json"
    google_client_id: str = ""  # Loaded from .env
    google_client_secret: str = ""  # Loaded from .env
    google_api_key: str = ""  # Loaded from .env

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "ChangeThisSecretForProduction"

    # User Management
    max_users: int = 5

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False
