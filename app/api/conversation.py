"""
Conversation API routes.
Handles text-based interaction with AI and conversation state management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.models import User
from app.utils.dependencies import get_current_user
from app.services.conversation_service import conversation_service


router = APIRouter(prefix="/conversation", tags=["Conversation"])


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    include_memory: bool = True
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    message: str
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class MessageModel(BaseModel):
    """Model for a conversation message."""
    id: Optional[str] = None
    role: str
    content: str
    timestamp: Optional[str] = None
    session_id: Optional[str] = None


class IntentAnalysis(BaseModel):
    """Model for intent analysis result."""
    type: str
    is_acknowledgment: bool
    is_command: bool
    is_interruption: bool
    confidence: float


# ==================== Endpoints ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Send a message and get an AI response.
    
    This is the main conversation endpoint. Features:
    - Context-aware responses using conversation history
    - Long-term memory integration
    - Configurable AI model and parameters
    
    Args:
        request: Chat request with message and options
        current_user: Authenticated user
        
    Returns:
        AI response with usage statistics
    """
    try:
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        result = await conversation_service.chat(
            user_id=current_user.uid,
            message=request.message,
            session_id=request.session_id,
            system_prompt=request.system_prompt,
            include_memory=request.include_memory,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get conversation history for the current user.
    
    Args:
        session_id: Optional filter by session
        limit: Maximum number of messages (default 50, max 100)
        current_user: Authenticated user
        
    Returns:
        List of conversation messages
    """
    if limit > 100:
        limit = 100
    
    history = await conversation_service.get_conversation_history(
        user_id=current_user.uid,
        session_id=session_id,
        limit=limit
    )
    
    return history


@router.delete("/history")
async def clear_conversation_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear conversation history.
    
    Args:
        session_id: Optional session to clear (None = clear all)
        current_user: Authenticated user
        
    Returns:
        Result with count of cleared messages
    """
    result = await conversation_service.clear_conversation(
        user_id=current_user.uid,
        session_id=session_id
    )
    
    return result


@router.post("/intent", response_model=IntentAnalysis)
async def analyze_intent(
    message: str,
    current_user: User = Depends(get_current_user)
) -> IntentAnalysis:
    """
    Analyze user intent from a message.
    
    Useful for:
    - Detecting interruptions during TTS playback
    - Classifying messages (command, question, acknowledgment)
    - Understanding user intentions
    
    Args:
        message: Message to analyze
        current_user: Authenticated user
        
    Returns:
        Intent analysis with type and confidence
    """
    if not message or len(message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    result = await conversation_service.analyze_intent(message)
    return IntentAnalysis(**result)


@router.post("/compress-memory")
async def compress_memory(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compress short-term conversation history to long-term memory.
    
    This endpoint:
    1. Summarizes recent conversations using AI
    2. Extracts key facts and preferences
    3. Saves them to long-term memory
    4. Helps maintain context across sessions
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Compression result with summary and saved facts
    """
    try:
        result = await conversation_service.compress_memory(current_user.uid)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory compression failed: {str(e)}"
        )
