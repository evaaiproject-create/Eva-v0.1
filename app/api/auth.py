"""
Authentication API routes.
Handles user registration and login with Google OAuth.
"""
from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict
from fastapi.responses import JSONResponse
import httpx

from app.models import UserRegistration, LoginRequest, TokenResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Google OAuth2 configuration
GOOGLE_CLIENT_ID = "your-google-client-id"  # Replace with actual client ID
GOOGLE_CLIENT_SECRET = "your-google-client-secret"  # Replace with actual client secret
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "https://ai-assist-81503423918.europe-west1.run.app/auth/callback"  # Replace with your backend URL

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(registration: UserRegistration) -> TokenResponse:
    """
    Register a new user with Google OAuth.
    
    This endpoint:
    1. Verifies the Google ID token
    2. Checks if user limit has been reached (max 5 users by default)
    3. Creates a new user in Firestore
    4. Returns an access token for the user
    
    Args:
        registration: UserRegistration with Google ID token and optional device_id
        
    Returns:
        TokenResponse with access token and user information
        
    Raises:
        HTTPException: 
            - 400 if token is invalid
            - 409 if user already exists
            - 403 if user limit reached
    """
    try:
        user, access_token = await auth_service.register_user(
            registration.id_token,
            registration.device_id
        )
        
        return TokenResponse(
            access_token=access_token,
            user=user
        )
        
    except ValueError as e:
        error_msg = str(e)
        
        if "already registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        elif "limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest) -> TokenResponse:
    """
    Login an existing user with Google OAuth.
    
    This endpoint:
    1. Verifies the Google ID token
    2. Retrieves the user from Firestore
    3. Updates last login timestamp
    4. Returns an access token for the user
    
    Args:
        login_request: LoginRequest with Google ID token and optional device_id
        
    Returns:
        TokenResponse with access token and user information
        
    Raises:
        HTTPException:
            - 400 if token is invalid
            - 404 if user not found
    """
    try:
        user, access_token = await auth_service.login_user(
            login_request.id_token,
            login_request.device_id
        )
        
        return TokenResponse(
            access_token=access_token,
            user=user
        )
        
    except ValueError as e:
        error_msg = str(e)
        
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.get("/verify")
async def verify_token(token: str) -> Dict[str, bool]:
    """
    Verify if a JWT token is valid.
    
    Args:
        token: JWT access token to verify
        
    Returns:
        Dictionary with valid: true/false
    """
    user = await auth_service.get_current_user(token)
    return {"valid": user is not None}


@router.get("/callback")
async def google_auth_callback(request: Request):
    """
    Handle OAuth2 callback from Google.
    
    This endpoint:
    1. Extracts the authorization code from the request
    2. Exchanges the authorization code for an access token and ID token
    3. Returns the tokens to the requester
    """
    # Extract the authorization code from the query parameters
    query_params = dict(request.query_params)
    auth_code = query_params.get("code")

    if not auth_code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Exchange the authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URI, data={
            "code": auth_code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        })

        if token_response.status_code != 200:
            raise HTTPException(status_code=token_response.status_code, detail="Failed to exchange authorization code")

        token_data = token_response.json()

    # Extract tokens from the response
    access_token = token_data.get("access_token")
    id_token = token_data.get("id_token")

    # Optional: Return tokens or redirect the user to another page
    return JSONResponse(content={"access_token": access_token, "id_token": id_token, "message": "OAuth2 callback handled successfully"})
