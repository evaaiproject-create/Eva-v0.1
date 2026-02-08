"""
================================================================================
UPDATED CONFIGURATION MANAGEMENT FOR EVA BACKEND
================================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    """
    Application settings with robust defaults to prevent Cloud Run startup crashes.
    """
    
    # ===== GOOGLE CLOUD CONFIGURATION =====
    google_cloud_project: str = Field(default="eva-backend-service")
    
    # Set to empty string by default so it doesn't crash if file is missing
    google_application_credentials: str = Field(default="")
    
    google_client_id: str = Field(default="81503423918-3sujbguhqjn6ns89hjb3858t92aksher.apps.googleusercontent.com")
    google_client_secret: str = Field(default="")
    google_api_key: str = Field(default="")

    # ===== API CONFIGURATION =====
    api_host: str = Field(default="0.0.0.0")
    
    # Use 8080 as default for Cloud Run compatibility
    api_port: int = Field(default=8080)
    
    api_secret_key: str = Field(default="762c83f5332d4cb184812a4ec3e2dc9efe8f5d1b6fde73e5f8b03c7d4a114e96")

    # ===== USER MANAGEMENT =====
    max_users: int = Field(default=5)

    # ===== CORS CONFIGURATION =====
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")

    # ===== ENVIRONMENT =====
    environment: str = Field(default="production")

    # ===== COMPUTED PROPERTIES =====
    @property
    def cors_origins_list(self) -> List[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    # Modern Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore" # This prevents crashes if extra variables are found
    )

# Create singleton settings instance
settings = Settings()
