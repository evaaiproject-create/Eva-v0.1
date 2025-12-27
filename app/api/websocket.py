"""
WebSocket API for real-time speech communication.
Handles bidirectional audio streaming for STT and TTS.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any, Optional
import json
import base64

from app.config import settings
from app.services.auth_service import auth_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.conversation_service import conversation_service
from app.services.memory_service import memory_service


router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    
    Features:
    - Connection tracking per user
    - Multi-device support
    - Broadcast capabilities
    """
    
    def __init__(self):
        """Initialize connection manager."""
        # Active connections: {user_id: {device_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, device_id: str):
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            device_id: Device identifier
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][device_id] = websocket
    
    def disconnect(self, user_id: str, device_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            user_id: User identifier
            device_id: Device identifier
        """
        if user_id in self.active_connections:
            if device_id in self.active_connections[user_id]:
                del self.active_connections[user_id][device_id]
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str, device_id: str):
        """
        Send a message to a specific device.
        
        Args:
            message: Message to send
            user_id: User identifier
            device_id: Device identifier
        """
        if user_id in self.active_connections:
            if device_id in self.active_connections[user_id]:
                websocket = self.active_connections[user_id][device_id]
                await websocket.send_json(message)
    
    async def broadcast_to_user(self, message: dict, user_id: str, exclude_device: Optional[str] = None):
        """
        Broadcast a message to all devices of a user.
        
        Args:
            message: Message to send
            user_id: User identifier
            exclude_device: Optional device to exclude
        """
        if user_id in self.active_connections:
            for device_id, websocket in self.active_connections[user_id].items():
                if device_id != exclude_device:
                    await websocket.send_json(message)
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get number of active connections.
        
        Args:
            user_id: Optional user to count connections for
            
        Returns:
            Number of active connections
        """
        if user_id:
            return len(self.active_connections.get(user_id, {}))
        
        return sum(len(devices) for devices in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


async def authenticate_websocket(token: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a WebSocket connection using JWT token.
    
    Args:
        token: JWT access token
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = await auth_service.get_current_user(token)
    if user:
        return {"uid": user.uid, "email": user.email}
    return None


@router.websocket("/speech/{device_id}")
async def websocket_speech(
    websocket: WebSocket,
    device_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time speech communication.
    
    Protocol:
    1. Client connects with device_id and token (query param)
    2. Server sends: {"type": "connected", "device_id": "..."}
    3. Client sends audio: {"type": "audio", "data": "<base64>", "language": "en-US"}
    4. Server responds with transcription: {"type": "transcription", "text": "...", "confidence": 0.95}
    5. Client can request TTS: {"type": "synthesize", "text": "Hello"}
    6. Server responds with audio: {"type": "audio", "data": "<base64>", "content_type": "audio/mp3"}
    7. For chat: {"type": "chat", "message": "Hello Eva"}
    8. Server responds: {"type": "response", "text": "Hi! How can I help?", "audio": "<base64>"}
    
    Message Types (Client -> Server):
    - audio: Audio data for transcription
    - synthesize: Text for TTS
    - chat: Message for AI conversation
    - ping: Keepalive
    - interrupt: Signal to stop current TTS
    
    Message Types (Server -> Client):
    - connected: Connection established
    - transcription: STT result
    - audio: TTS audio data
    - response: AI response (with optional audio)
    - error: Error message
    - pong: Keepalive response
    - interrupted: TTS interrupted
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    user_data = await authenticate_websocket(token)
    if not user_data:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = user_data["uid"]
    
    # Connect
    await manager.connect(websocket, user_id, device_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "device_id": device_id,
            "user_id": user_id,
            "message": "Connected to Eva speech service"
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                # Keepalive
                await websocket.send_json({"type": "pong"})
            
            elif message_type == "audio":
                # Transcribe audio
                await handle_audio_message(websocket, user_id, device_id, data)
            
            elif message_type == "synthesize":
                # Text-to-speech
                await handle_synthesize_message(websocket, user_id, data)
            
            elif message_type == "chat":
                # AI conversation
                await handle_chat_message(websocket, user_id, device_id, data)
            
            elif message_type == "interrupt":
                # Handle interruption
                await websocket.send_json({
                    "type": "interrupted",
                    "message": "Playback interrupted"
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, device_id)
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except Exception:
            pass
        manager.disconnect(user_id, device_id)


async def handle_audio_message(
    websocket: WebSocket,
    user_id: str,
    device_id: str,
    data: dict
):
    """
    Handle incoming audio for transcription.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        device_id: Device identifier
        data: Message data with audio
    """
    try:
        audio_base64 = data.get("data", "")
        language = data.get("language", "en-US")
        engine = data.get("engine")
        
        if not audio_base64:
            await websocket.send_json({
                "type": "error",
                "error": "No audio data provided"
            })
            return
        
        # Decode and transcribe
        audio_data = base64.b64decode(audio_base64)
        result = await stt_service.transcribe(
            audio_data=audio_data,
            language=language,
            engine=engine
        )
        
        if "error" in result:
            await websocket.send_json({
                "type": "error",
                "error": result["error"]
            })
        else:
            # Analyze intent
            intent = await conversation_service.analyze_intent(result["text"])
            
            await websocket.send_json({
                "type": "transcription",
                "text": result["text"],
                "confidence": result["confidence"],
                "language": result["language"],
                "engine": result.get("engine"),
                "intent": intent
            })
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": f"Transcription failed: {str(e)}"
        })


async def handle_synthesize_message(
    websocket: WebSocket,
    user_id: str,
    data: dict
):
    """
    Handle TTS synthesis request.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        data: Message data with text
    """
    try:
        text = data.get("text", "")
        voice = data.get("voice")
        language = data.get("language", "en-US")
        engine = data.get("engine")
        
        if not text:
            await websocket.send_json({
                "type": "error",
                "error": "No text provided"
            })
            return
        
        result = await tts_service.synthesize(
            text=text,
            voice=voice,
            language=language,
            engine=engine
        )
        
        if "error" in result:
            await websocket.send_json({
                "type": "error",
                "error": result["error"]
            })
        else:
            await websocket.send_json({
                "type": "audio",
                "data": result["audio_base64"],
                "content_type": result["content_type"],
                "duration_seconds": result["duration_seconds"],
                "engine": result.get("engine")
            })
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": f"Synthesis failed: {str(e)}"
        })


async def handle_chat_message(
    websocket: WebSocket,
    user_id: str,
    device_id: str,
    data: dict
):
    """
    Handle AI chat message.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        device_id: Device identifier
        data: Message data
    """
    try:
        message = data.get("message", "")
        include_audio = data.get("include_audio", False)
        session_id = data.get("session_id")
        
        if not message:
            await websocket.send_json({
                "type": "error",
                "error": "No message provided"
            })
            return
        
        # Get AI response
        chat_result = await conversation_service.chat(
            user_id=user_id,
            message=message,
            session_id=session_id
        )
        
        response = {
            "type": "response",
            "text": chat_result.get("message", ""),
            "success": chat_result.get("success", False)
        }
        
        if not chat_result.get("success"):
            response["error"] = chat_result.get("error")
        
        # Optionally include audio
        if include_audio and chat_result.get("success"):
            tts_result = await tts_service.synthesize(
                text=chat_result["message"],
                language=data.get("language", "en-US")
            )
            
            if "error" not in tts_result:
                response["audio"] = tts_result["audio_base64"]
                response["audio_content_type"] = tts_result["content_type"]
                response["audio_duration"] = tts_result["duration_seconds"]
        
        await websocket.send_json(response)
        
        # Broadcast to other devices (optional)
        if data.get("sync_devices", False):
            await manager.broadcast_to_user(
                {
                    "type": "sync",
                    "event": "new_message",
                    "from_device": device_id,
                    "message": message,
                    "response": chat_result.get("message", "")
                },
                user_id,
                exclude_device=device_id
            )
    
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": f"Chat failed: {str(e)}"
        })


# REST endpoint for WebSocket info
@router.get("/info")
async def websocket_info():
    """
    Get WebSocket endpoint information.
    
    Returns:
        WebSocket connection details and protocol
    """
    return {
        "endpoint": "/ws/speech/{device_id}",
        "authentication": "Query parameter: ?token=<jwt_token>",
        "protocol": {
            "client_to_server": {
                "audio": "Send audio for transcription",
                "synthesize": "Request TTS for text",
                "chat": "Send message for AI response",
                "ping": "Keepalive",
                "interrupt": "Stop current TTS playback"
            },
            "server_to_client": {
                "connected": "Connection established",
                "transcription": "STT result",
                "audio": "TTS audio data",
                "response": "AI chat response",
                "error": "Error message",
                "pong": "Keepalive response",
                "interrupted": "TTS interrupted",
                "sync": "Cross-device sync event"
            }
        },
        "example_messages": {
            "send_audio": {
                "type": "audio",
                "data": "<base64_encoded_audio>",
                "language": "en-US"
            },
            "request_tts": {
                "type": "synthesize",
                "text": "Hello, how can I help you?",
                "language": "en-US"
            },
            "chat": {
                "type": "chat",
                "message": "What's the weather like?",
                "include_audio": True
            }
        },
        "active_connections": manager.get_connection_count()
    }
