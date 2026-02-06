"""
================================================================================
CHAT API ENDPOINTS FOR EVA
================================================================================

PURPOSE:
    This file defines the web API endpoints (URLs) that the Android app uses
    to communicate with EVA. Think of it as the "front door" to EVA's brain.

ENDPOINTS DEFINED HERE:
    POST /chat/send          - Send a message and get a response
    POST /chat/send/stream   - Send a message and stream the response (for voice)
    GET  /chat/history       - Get chat history for a conversation
    POST /chat/new           - Start a new conversation
    GET  /chat/conversations - List all conversations for a user
    DELETE /chat/{id}        - Delete a conversation

FLOW OF A CHAT MESSAGE:
    1. User types "Hello" in Android app
    2. Android app sends POST request to /chat/send with:
       - message: "Hello"
       - conversation_id: "conv_123" (optional)
       - Authorization header with JWT token
    3. This file receives the request
    4. Validates the user's authentication token
    5. Saves the message to Firestore (for sync/backup)
    6. Sends message to GeminiService
    7. Gets response from Gemini
    8. Saves response to Firestore
    9. Returns response to Android app

AUTHENTICATION:
    All endpoints require a valid JWT token in the Authorization header.
    Example: "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
    
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from app.services.gemini_service import gemini_service
from app.services.firestore_service import firestore_service
from app.services.auth_service import auth_service
from app.models import User


# ================================================================================
# REQUEST/RESPONSE MODELS
# ================================================================================
# These classes define the shape of data coming in (requests) and going out (responses)
# Think of them as "contracts" - they ensure data is formatted correctly

class ChatMessageRequest(BaseModel):
    """
    Model for incoming chat message requests.
    
    WHAT THE ANDROID APP SENDS:
        {
            "message": "Hello EVA, how are you?",
            "conversation_id": "conv_abc123"  // optional
        }
    
    FIELDS:
        message (str): The text the user typed. Required. Must be 1-10000 chars.
        conversation_id (str, optional): ID of existing conversation to continue.
                                         If not provided, uses default conversation.
    """
    message: str = Field(
        ...,  # ... means required
        min_length=1,
        max_length=10000,
        description="The message text from the user"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID to continue an existing chat"
    )


class ChatMessageResponse(BaseModel):
    """
    Model for chat message responses.
    
    WHAT THE ANDROID APP RECEIVES:
        {
            "message_id": "msg_xyz789",
            "conversation_id": "conv_abc123",
            "response": "Hello! I'm doing great, thanks for asking!",
            "timestamp": "2024-01-15T10:30:00Z",
            "emotion_detected": "friendly"
        }
    
    FIELDS:
        message_id: Unique ID for this message (for tracking)
        conversation_id: Which conversation this belongs to
        response: EVA's response text
        timestamp: When the response was generated
        emotion_detected: Detected emotional tone (future feature)
    """
    message_id: str
    conversation_id: str
    response: str
    timestamp: datetime
    emotion_detected: Optional[str] = None


class ConversationInfo(BaseModel):
    """
    Information about a conversation.
    
    USED FOR:
        Listing user's previous conversations in the app's sidebar
    
    FIELDS:
        conversation_id: Unique identifier
        title: Display title (usually first message or summary)
        created_at: When conversation started
        updated_at: When last message was sent
        message_count: How many messages in this conversation
    """
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class NewConversationRequest(BaseModel):
    """
    Request to start a new conversation.
    
    FIELDS:
        title (str, optional): Custom title for the conversation
                              If not provided, will be auto-generated
    """
    title: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional custom title for the conversation"
    )


class NewConversationResponse(BaseModel):
    """
    Response when creating a new conversation.
    
    FIELDS:
        conversation_id: The new conversation's unique ID
        title: The conversation's title
        created_at: When it was created
    """
    conversation_id: str
    title: str
    created_at: datetime


# ================================================================================
# AUTHENTICATION HELPER
# ================================================================================

async def get_current_user(authorization: str = None) -> User:
    """
    Validate the JWT token and return the current user.
    
    HOW AUTHENTICATION WORKS:
        1. Android app sends request with header:
           "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
        2. This function extracts the token
        3. Decodes and validates it
        4. Returns the User object
    
    IF TOKEN IS INVALID:
        Raises 401 Unauthorized error - app must re-login
    
    PARAMETERS:
        authorization: The Authorization header value
    
    RETURNS:
        User object with user's info (uid, email, etc.)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Extract token (remove "Bearer " prefix)
    token = authorization.replace("Bearer ", "")
    
    # Decode the token
    payload = auth_service.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user from database
    user = await firestore_service.get_user(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ================================================================================
# ROUTER SETUP
# ================================================================================

# Create the API router with a prefix and tags for documentation
router = APIRouter(
    prefix="/chat",  # All routes will be /chat/...
    tags=["Chat"],   # Groups these endpoints in API docs
    responses={
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"}
    }
)


# ================================================================================
# ENDPOINTS
# ================================================================================

@router.post(
    "/send",
    response_model=ChatMessageResponse,
    summary="Send a message to EVA",
    description="""
    Send a text message to EVA and receive a response.
    
    This is the main endpoint for chat functionality. It:
    1. Validates your authentication
    2. Saves your message to Firestore for backup/sync
    3. Sends the message to Gemini AI
    4. Saves EVA's response to Firestore
    5. Returns the response
    
    **Note:** Messages are stored for cross-device sync and conversation history.
    """
)
async def send_message(
    request: ChatMessageRequest,
    authorization: str = None
) -> ChatMessageResponse:
    """
    Send a message to EVA and get a response.
    
    THE MAIN CHAT ENDPOINT - Most important function in this file!
    
    STEP-BY-STEP PROCESS:
        1. Authenticate the user (check their login token)
        2. Generate unique IDs for message tracking
        3. Save user's message to Firestore
        4. Send message to Gemini AI
        5. Save EVA's response to Firestore
        6. Return response to the app
    
    PARAMETERS:
        request: Contains the message and optional conversation_id
        authorization: JWT token from the Authorization header
    
    RETURNS:
        ChatMessageResponse with EVA's response
    """
    # Step 1: Authenticate the user
    user = await get_current_user(authorization)
    
    # Step 2: Generate IDs
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow()
    
    # Step 3: Save user's message to Firestore
    # This enables:
    # - Cross-device sync (see chat on phone and tablet)
    # - Chat history (reload app and see previous messages)
    # - Backup (messages aren't lost if app crashes)
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=message_id,
        content=request.message,
        role="user",  # Mark as user's message
        timestamp=timestamp
    )
    
    # Step 4: Send to Gemini and get response
    response_text = await gemini_service.send_message(
        message=request.message,
        user_id=user.uid,
        conversation_id=conversation_id
    )
    
    # Step 5: Save EVA's response to Firestore
    response_id = f"msg_{uuid.uuid4().hex[:12]}"
    response_timestamp = datetime.utcnow()
    
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=response_id,
        content=response_text,
        role="assistant",  # Mark as EVA's message
        timestamp=response_timestamp
    )
    
    # Update conversation metadata (for listing in sidebar)
    await firestore_service.update_conversation_metadata(
        user_id=user.uid,
        conversation_id=conversation_id,
        last_message=response_text[:50] + "..." if len(response_text) > 50 else response_text
    )
    
    # Step 6: Return the response
    return ChatMessageResponse(
        message_id=response_id,
        conversation_id=conversation_id,
        response=response_text,
        timestamp=response_timestamp,
        emotion_detected=None  # Future feature
    )


@router.post(
    "/send/stream",
    summary="Send a message and stream the response",
    description="""
    Send a message and receive the response as a stream.
    
    **Use case:** Real-time voice calls where you want to start speaking
    before the entire response is generated.
    
    **Response format:** Server-Sent Events (SSE) with JSON chunks
    """
)
async def send_message_stream(
    request: ChatMessageRequest,
    authorization: str = None
):
    """
    Send a message and stream EVA's response in real-time.
    
    FOR VOICE CALLS - Returns words as they're generated.
    
    HOW STREAMING WORKS:
        Instead of waiting for complete response, we send text chunks
        as the AI generates them. This reduces perceived latency.
    
    RESPONSE FORMAT:
        Server-Sent Events (SSE) - each chunk is:
        data: {"text": "Hello", "done": false}
        data: {"text": " there!", "done": false}
        data: {"text": "", "done": true}
    """
    # Authenticate user
    user = await get_current_user(authorization)
    
    # Generate IDs
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    
    # Save user's message
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    await firestore_service.save_chat_message(
        user_id=user.uid,
        conversation_id=conversation_id,
        message_id=message_id,
        content=request.message,
        role="user",
        timestamp=datetime.utcnow()
    )
    
    async def generate():
        """
        Async generator that yields SSE-formatted chunks.
        """
        full_response = ""
        
        # Stream from Gemini
        async for chunk in gemini_service.send_message_stream(
            message=request.message,
            user_id=user.uid,
            conversation_id=conversation_id
        ):
            full_response += chunk
            # Format as SSE
            yield f"data: {json.dumps({'text': chunk, 'done': False})}\n\n"
        
        # Signal completion
        yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"
        
        # Save complete response to Firestore
        await firestore_service.save_chat_message(
            user_id=user.uid,
            conversation_id=conversation_id,
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            content=full_response,
            role="assistant",
            timestamp=datetime.utcnow()
        )
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get(
    "/history/{conversation_id}",
    summary="Get chat history",
    description="Retrieve all messages in a conversation, ordered by timestamp."
)
async def get_chat_history(
    conversation_id: str,
    limit: int = 50,
    authorization: str = None
) -> List[Dict[str, Any]]:
    """
    Get chat history for a conversation.
    
    USED FOR:
        - Loading previous messages when opening a chat
        - Syncing messages across devices
    
    PARAMETERS:
        conversation_id: Which conversation to get history for
        limit: Maximum number of messages to return (default 50)
        authorization: JWT token
    
    RETURNS:
        List of messages, newest first
    """
    user = await get_current_user(authorization)
    
    messages = await firestore_service.get_chat_messages(
        user_id=user.uid,
        conversation_id=conversation_id,
        limit=limit
    )
    
    return messages


@router.post(
    "/new",
    response_model=NewConversationResponse,
    summary="Start a new conversation",
    description="Create a new conversation. Clears AI memory for fresh start."
)
async def new_conversation(
    request: NewConversationRequest = None,
    authorization: str = None
) -> NewConversationResponse:
    """
    Start a new conversation.
    
    WHAT THIS DOES:
        1. Creates a new conversation ID
        2. Clears any existing AI memory (fresh start)
        3. Creates metadata in Firestore
    
    WHEN USED:
        - User taps "New Chat" in the app
        - User wants to start fresh without previous context
    """
    user = await get_current_user(authorization)
    
    # Generate new conversation ID
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow()
    
    # Clear any existing Gemini memory for this conversation
    gemini_service.clear_conversation(user.uid, conversation_id)
    
    # Create conversation metadata in Firestore
    title = request.title if request and request.title else "New Conversation"
    
    await firestore_service.create_conversation(
        user_id=user.uid,
        conversation_id=conversation_id,
        title=title,
        created_at=timestamp
    )
    
    return NewConversationResponse(
        conversation_id=conversation_id,
        title=title,
        created_at=timestamp
    )


@router.get(
    "/conversations",
    response_model=List[ConversationInfo],
    summary="List all conversations",
    description="Get all conversations for the current user, ordered by most recent."
)
async def list_conversations(
    authorization: str = None
) -> List[ConversationInfo]:
    """
    List all conversations for the current user.
    
    USED FOR:
        Populating the conversation list in the app's navigation drawer
    
    RETURNS:
        List of conversations with titles and timestamps
    """
    user = await get_current_user(authorization)
    
    conversations = await firestore_service.get_user_conversations(user.uid)
    
    return [
        ConversationInfo(
            conversation_id=conv["conversation_id"],
            title=conv.get("title", "Untitled"),
            created_at=conv["created_at"],
            updated_at=conv.get("updated_at", conv["created_at"]),
            message_count=conv.get("message_count", 0)
        )
        for conv in conversations
    ]


@router.delete(
    "/{conversation_id}",
    summary="Delete a conversation",
    description="Permanently delete a conversation and all its messages."
)
async def delete_conversation(
    conversation_id: str,
    authorization: str = None
) -> Dict[str, str]:
    """
    Delete a conversation.
    
    WHAT THIS DOES:
        1. Verifies the conversation belongs to the user
        2. Deletes all messages in the conversation
        3. Deletes conversation metadata
        4. Clears Gemini memory
    
    WARNING: This is permanent and cannot be undone!
    """
    user = await get_current_user(authorization)
    
    # Delete from Firestore
    await firestore_service.delete_conversation(
        user_id=user.uid,
        conversation_id=conversation_id
    )
    
    # Clear Gemini memory
    gemini_service.clear_conversation(user.uid, conversation_id)
    
    return {"message": f"Conversation {conversation_id} deleted successfully"}
