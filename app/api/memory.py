"""
Memory management API routes.
Handles short-term context and long-term memory operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.models import User
from app.utils.dependencies import get_current_user
from app.services.memory_service import memory_service


router = APIRouter(prefix="/memory", tags=["Memory"])


# ==================== Request/Response Models ====================

class MemoryCreate(BaseModel):
    """Request model for creating a memory."""
    category: str = Field(..., description="Category: preference, interest, event, goal, fact")
    content: str = Field(..., description="Memory content")
    importance: int = Field(default=5, ge=1, le=10, description="Importance score 1-10")
    metadata: Optional[Dict[str, Any]] = None


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""
    content: Optional[str] = None
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    id: str
    category: str
    content: str
    importance: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== Long-Term Memory Endpoints ====================

@router.post("/", response_model=Dict[str, Any])
async def create_memory(
    memory: MemoryCreate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Save information to long-term memory.
    
    Long-term memory stores persistent facts about the user:
    - Preferences (e.g., "Prefers dark mode")
    - Interests (e.g., "Interested in machine learning")
    - Events (e.g., "Has a meeting on Friday")
    - Goals (e.g., "Wants to learn Spanish")
    - Facts (e.g., "Lives in New York")
    
    Args:
        memory: Memory content and metadata
        current_user: Authenticated user
        
    Returns:
        Created memory document
    """
    try:
        if not memory.content or len(memory.content.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Memory content is required"
            )
        
        result = await memory_service.save_memory(
            user_id=current_user.uid,
            category=memory.category,
            content=memory.content,
            importance=memory.importance,
            metadata=memory.metadata
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save memory: {str(e)}"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def get_memories(
    category: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get long-term memories for the current user.
    
    Args:
        category: Optional filter by category
        limit: Maximum number of memories (default 50, max 100)
        current_user: Authenticated user
        
    Returns:
        List of memory documents sorted by importance
    """
    if limit > 100:
        limit = 100
    
    memories = await memory_service.get_memories(
        user_id=current_user.uid,
        category=category,
        limit=limit
    )
    
    return memories


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_memories(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Search long-term memories by keyword.
    
    Args:
        query: Search query
        limit: Maximum results (default 10, max 50)
        current_user: Authenticated user
        
    Returns:
        Matching memories
    """
    if not query or len(query.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query is required"
        )
    
    if limit > 50:
        limit = 50
    
    results = await memory_service.search_memories(
        user_id=current_user.uid,
        query=query,
        limit=limit
    )
    
    return results


@router.get("/{memory_id}", response_model=Dict[str, Any])
async def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: Memory document ID
        current_user: Authenticated user
        
    Returns:
        Memory document
    """
    memories = await memory_service.get_memories(
        user_id=current_user.uid,
        limit=100
    )
    
    for memory in memories:
        if memory.get("id") == memory_id:
            return memory
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Memory not found"
    )


@router.put("/{memory_id}", response_model=Dict[str, Any])
async def update_memory(
    memory_id: str,
    updates: MemoryUpdate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update a long-term memory.
    
    Args:
        memory_id: Memory document ID
        updates: Fields to update
        current_user: Authenticated user
        
    Returns:
        Updated memory document
    """
    update_data = {}
    
    if updates.content is not None:
        update_data["content"] = updates.content
    if updates.importance is not None:
        update_data["importance"] = updates.importance
    if updates.metadata is not None:
        update_data["metadata"] = updates.metadata
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )
    
    result = await memory_service.update_memory(
        user_id=current_user.uid,
        memory_id=memory_id,
        updates=update_data
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    return result


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a long-term memory.
    
    Args:
        memory_id: Memory document ID
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    success = await memory_service.delete_memory(
        user_id=current_user.uid,
        memory_id=memory_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    return {"message": "Memory deleted successfully"}


# ==================== Short-Term Context Endpoints ====================

@router.get("/context/recent", response_model=List[Dict[str, Any]])
async def get_recent_context(
    session_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get recent short-term context (conversation messages).
    
    Args:
        session_id: Optional filter by session
        limit: Maximum messages (default 20, max 50)
        current_user: Authenticated user
        
    Returns:
        Recent messages
    """
    if limit > 50:
        limit = 50
    
    messages = await memory_service.get_recent_messages(
        user_id=current_user.uid,
        limit=limit,
        session_id=session_id
    )
    
    return messages


@router.delete("/context")
async def clear_short_term_context(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear short-term context.
    
    Args:
        session_id: Optional session to clear (None = clear all)
        current_user: Authenticated user
        
    Returns:
        Result with count of cleared messages
    """
    count = await memory_service.clear_short_term_context(
        user_id=current_user.uid,
        session_id=session_id
    )
    
    return {
        "success": True,
        "messages_cleared": count
    }


# ==================== AI Memory Operations ====================

@router.post("/summarize")
async def summarize_conversation(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Summarize recent conversations using AI.
    
    This extracts key facts without saving them.
    Use /compress to also save to long-term memory.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Summary with extracted facts and topics
    """
    try:
        result = await memory_service.summarize_conversation(current_user.uid)
        
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
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/compress")
async def compress_to_long_term(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compress short-term context to long-term memory.
    
    This endpoint:
    1. Summarizes recent conversations using AI
    2. Extracts key facts (preferences, interests, events, goals)
    3. Saves them to long-term memory with importance scores
    
    Best used periodically or when switching contexts.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Compression result with summary and saved facts count
    """
    try:
        result = await memory_service.compress_to_long_term(current_user.uid)
        
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
