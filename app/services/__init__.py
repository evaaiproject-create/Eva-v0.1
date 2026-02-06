"""
================================================================================
SERVICES PACKAGE INITIALIZATION
================================================================================

PURPOSE:
    This file makes the app/services/ directory a Python package and exports
    all service modules.

SERVICES:
    firestore_service - Database operations (users, messages, sessions)
    auth_service      - Authentication and JWT token management
    gemini_service    - Gemini AI communication (NEW!)
    function_registry - Dynamic function calling framework

================================================================================
"""

from app.services.firestore_service import firestore_service
from app.services.auth_service import auth_service
from app.services.gemini_service import gemini_service

__all__ = ["firestore_service", "auth_service", "gemini_service"]
