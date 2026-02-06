"""
================================================================================
EVA BACKEND - MAIN APPLICATION
================================================================================

PURPOSE:
    This is the entry point for the Eva backend server. When you run the server,
    this file is what starts everything up.

WHAT THIS FILE DOES:
    1. Creates the FastAPI application
    2. Configures security settings (CORS)
    3. Connects all the API routers (auth, users, sessions, functions, chat)
    4. Defines basic endpoints (health check, root info)
    5. Handles global errors

TO RUN THE SERVER:
    Development: python main.py
    Production:  Deployed automatically on Cloud Run

ENDPOINTS SUMMARY:
    /           - API info
    /health     - Health check
    /auth/*     - Authentication (login, register)
    /users/*    - User management
    /sessions/* - Cross-device session sync
    /functions/*- Function calling framework
    /chat/*     - Chat with EVA (NEW!)
    /docs       - Interactive API documentation

================================================================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api import auth, users, sessions, functions
from app.api import chat  # NEW: Import chat router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    WHAT THIS DOES:
        - Runs code when the server starts up
        - Runs code when the server shuts down
    
    STARTUP:
        Prints configuration information for debugging
    
    SHUTDOWN:
        Prints shutdown message
    """
    # ===== STARTUP =====
    print("=" * 60)
    print("🤖 EVA Backend Starting...")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Google Cloud Project: {settings.google_cloud_project}")
    print(f"Max Users: {settings.max_users}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"Chat Endpoint: Enabled ✓")  # NEW
    print("=" * 60)
    
    yield  # Server runs here
    
    # ===== SHUTDOWN =====
    print("\n🤖 EVA Backend Shutting Down...")


# Create the FastAPI application
app = FastAPI(
    title="Eva Backend API",
    description=(
        "Backend API for EVA - A personal assistant inspired by JARVIS and Baymax. "
        "Provides authentication, data persistence, cross-device sync, chat with AI, "
        "and function calling capabilities."
    ),
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your Android app to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routers
# Each router handles a different group of endpoints
app.include_router(auth.router)       # /auth/*
app.include_router(users.router)      # /users/*
app.include_router(sessions.router)   # /sessions/*
app.include_router(functions.router)  # /functions/*
app.include_router(chat.router)       # /chat/* (NEW!)


@app.get("/")
async def root():
    """
    Root endpoint - API information.
    
    RETURNS:
        Basic information about the API
    
    EXAMPLE RESPONSE:
        {
            "name": "Eva Backend API",
            "version": "0.1.0",
            "status": "operational",
            "description": "Personal assistant backend...",
            "documentation": "/docs"
        }
    """
    return {
        "name": "Eva Backend API",
        "version": "0.1.0",
        "status": "operational",
        "description": "Personal assistant backend inspired by JARVIS and Baymax",
        "documentation": "/docs",
        "features": [
            "Google OAuth Authentication",
            "Chat with Gemini AI",
            "Cross-device Session Sync",
            "Function Calling Framework"
        ]
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    PURPOSE:
        - Cloud Run uses this to verify the server is running
        - Monitoring systems ping this to check server health
    
    RETURNS:
        Server health status
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "max_users": settings.max_users
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    WHAT THIS DOES:
        If any unexpected error occurs, this catches it and returns
        a friendly error message instead of crashing.
    
    SECURITY:
        In production, doesn't expose error details to users
        In development, includes error message for debugging
    """
    print(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if not settings.is_production else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    # This is used for local development
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production  # Auto-reload in development
    )
