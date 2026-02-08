"""
================================================================================
AUTHENTICATION SERVICE FOR EVA BACKEND
================================================================================

PURPOSE:
    Handles all authentication-related operations:
    - Google OAuth ID token verification
    - JWT access token generation and validation
    - User registration and login
    - User limit enforcement

SECURITY LAYERS:
    Layer 1: Google ID Token Verification
        - The Android app signs the user in with Google
        - We verify the resulting ID token is legitimate and was
          issued for OUR app (google_client_id must match)

    Layer 2: JWT Access Tokens
        - After verification, we issue our own JWT signed with API_SECRET_KEY
        - All subsequent API calls use this JWT (not the Google token)
        - Tokens expire after 7 days

    Layer 3 (Future): Firebase App Check
        - Prevents unauthorized clients (curl, Postman, scrapers)
        - Only your real Android app can call the API

================================================================================
"""

from google.oauth2 import id_token
from google.auth.transport import requests
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.config import settings
from app.models import User, UserRole
from app.services.firestore_service import firestore_service


class AuthService:
    """
    Authentication service for Eva backend.

    Handles:
    - Google OAuth token verification
    - JWT token generation and validation
    - User registration and login
    - User limit enforcement
    """

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

    def __init__(self):
        """
        Initialize authentication service.

        Loads the Google Web Client ID and JWT signing key from settings.
        Validates that critical values are present at startup so failures
        are caught immediately rather than at the first login attempt.
        """
        self.google_client_id = settings.google_client_id
        self.secret_key = settings.api_secret_key

        # ---- Startup validation ------------------------------------------------
        # Fail fast if critical auth config is missing. This surfaces
        # misconfiguration at deploy time (Cloud Run logs) instead of at
        # the first user request.
        # ------------------------------------------------------------------------
        if not self.google_client_id:
            print(
                "⚠️  WARNING: GOOGLE_CLIENT_ID is not set. "
                "Google token verification will fail for all login attempts."
            )

        if self.secret_key == "ChangeThisSecretForProduction":
            print(
                "⚠️  WARNING: API_SECRET_KEY is using the default value. "
                "Generate a production key with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )

    # ===========================================================================
    # GOOGLE TOKEN VERIFICATION
    # ===========================================================================

    async def verify_google_token(self, id_token_string: str) -> Optional[dict]:
        """
        Verify a Google ID token and extract user information.

        This is the critical security gate — it proves that the token was
        genuinely issued by Google for a user who authenticated with our app.

        Args:
            id_token_string: Google ID token from the Android app's OAuth flow

        Returns:
            Dict with 'sub' (Google user ID), 'email', 'name', 'picture'
            None if the token is invalid or was not issued for our client ID
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_string,
                requests.Request(),
                self.google_client_id,
            )

            return {
                "sub": idinfo["sub"],               # Google user ID (stable, unique)
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
            }

        except ValueError as e:
            print(f"Google token verification failed: {e}")
            return None

    # ===========================================================================
    # JWT TOKEN MANAGEMENT
    # ===========================================================================

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a signed JWT access token.

        The token encodes the user's ID and email so we can identify them
        on every subsequent API request without hitting Google again.

        Args:
            data: Payload to encode (must include 'sub' for user ID)
            expires_delta: Custom lifetime; defaults to 7 days

        Returns:
            Encoded JWT string
        """
        to_encode = data.copy()

        expire = datetime.utcnow() + (
            expires_delta
            if expires_delta
            else timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, self.secret_key, algorithm=self.ALGORITHM)

    def decode_access_token(self, token: str) -> Optional[dict]:
        """
        Decode and verify a JWT access token.

        Args:
            token: JWT string from the Authorization header

        Returns:
            Decoded payload dict, or None if the token is invalid / expired
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.ALGORITHM])
        except JWTError:
            return None

    # ===========================================================================
    # REGISTRATION
    # ===========================================================================

    async def register_user(
        self,
        id_token_string: str,
        device_id: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Register a new user with a Google ID token.

        Flow:
            1. Verify the Google token → proves identity
            2. Check the user doesn't already exist → prevents duplicates
            3. Enforce user limit → personal-project guardrail
            4. Create user in Firestore
            5. Issue a JWT access token

        Args:
            id_token_string: Google ID token from the Android app
            device_id: Optional device identifier for cross-device sync

        Returns:
            Tuple of (User object, JWT access token string)

        Raises:
            ValueError: If token is invalid, user exists, or limit reached
        """
        # Verify Google token
        google_user = await self.verify_google_token(id_token_string)
        if not google_user:
            raise ValueError("Invalid Google ID token")

        # Check if user already exists
        existing_user = await firestore_service.get_user(google_user["sub"])
        if existing_user:
            raise ValueError("User already registered")

        # Check user limit
        user_count = await firestore_service.count_users()
        if user_count >= settings.max_users:
            raise ValueError(
                f"Maximum user limit ({settings.max_users}) reached"
            )

        # Create new user
        user = User(
            uid=google_user["sub"],
            email=google_user["email"],
            display_name=google_user.get("name"),
            role=UserRole.USER,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            devices=[device_id] if device_id else [],
        )

        # Save to Firestore
        await firestore_service.create_user(user)

        # Generate access token
        access_token = self.create_access_token(
            {"sub": user.uid, "email": user.email}
        )

        return user, access_token

    # ===========================================================================
    # LOGIN
    # ===========================================================================

    async def login_user(
        self,
        id_token_string: str,
        device_id: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Login an existing user with a Google ID token.

        Flow:
            1. Verify the Google token
            2. Look up the user in Firestore
            3. Update last-login timestamp
            4. Register device if new
            5. Issue a fresh JWT access token

        Args:
            id_token_string: Google ID token from the Android app
            device_id: Optional device identifier

        Returns:
            Tuple of (User object, JWT access token string)

        Raises:
            ValueError: If token is invalid or user not found
        """
        # Verify Google token
        google_user = await self.verify_google_token(id_token_string)
        if not google_user:
            raise ValueError("Invalid Google ID token")

        # Get user from Firestore
        user = await firestore_service.get_user(google_user["sub"])
        if not user:
            raise ValueError("User not found. Please register first.")

        # Update last login
        await firestore_service.update_user(
            user.uid, {"last_login": datetime.utcnow()}
        )

        # Add device if provided and not already registered
        if device_id:
            await firestore_service.add_device_to_user(user.uid, device_id)

        # Generate access token
        access_token = self.create_access_token(
            {"sub": user.uid, "email": user.email}
        )

        return user, access_token

    # ===========================================================================
    # TOKEN → USER LOOKUP
    # ===========================================================================

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Resolve a JWT access token to a User object.

        Used by the /auth/verify endpoint and internal helpers.

        Args:
            token: JWT access token

        Returns:
            User object, or None if token is invalid
        """
        payload = self.decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return await firestore_service.get_user(user_id)


# Global singleton — used by all API routes
auth_service = AuthService()
