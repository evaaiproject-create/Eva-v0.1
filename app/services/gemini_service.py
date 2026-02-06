"""
================================================================================
GEMINI AI SERVICE FOR EVA
================================================================================

PURPOSE:
    This file is the "brain" of EVA. It handles all communication with Google's 
    Gemini AI model. When a user sends a message, this service:
    1. Takes the user's message
    2. Sends it to Google's Gemini AI
    3. Returns the AI's response

WHAT IS GEMINI?
    Gemini is Google's advanced AI model (similar to ChatGPT). We use the 
    "gemini-2.0-flash" model which supports:
    - Text conversations (chat)
    - Emotional tone detection
    - Real-time streaming responses (for voice calls)

HOW IT WORKS:
    1. User types "Hello EVA" in the app
    2. App sends this to our Cloud Run backend
    3. Backend calls this GeminiService
    4. GeminiService sends the message to Google's Gemini API
    5. Gemini responds with intelligent text
    6. Response flows back to the user's app

CONFIGURATION:
    - Uses GOOGLE_API_KEY from environment variables
    - Model: gemini-2.0-flash (chosen for speed + emotional intelligence)

================================================================================
"""

import google.generativeai as genai
from typing import Optional, AsyncGenerator, Dict, Any, List
from datetime import datetime
import asyncio

from app.config import settings


class GeminiService:
    """
    Service class for interacting with Google's Gemini AI.
    
    This class manages:
    - Initializing the Gemini AI model
    - Sending messages and receiving responses
    - Maintaining conversation history for context
    - Streaming responses for real-time voice calls
    
    ATTRIBUTES:
        model_name (str): The Gemini model version we're using
        model: The initialized Gemini model object
        system_instruction (str): EVA's personality and behavior instructions
    
    USAGE EXAMPLE:
        service = GeminiService()
        response = await service.send_message("Hello!", user_id="user123")
        print(response)  # "Hello! I'm EVA, how can I help you today?"
    """
    
    def __init__(self):
        """
        Initialize the Gemini AI service.
        
        WHAT THIS DOES:
            1. Configures the Google AI library with our API key
            2. Sets up EVA's personality (system instruction)
            3. Creates the AI model instance
        
        NOTE: The API key comes from the GOOGLE_API_KEY environment variable.
              This is set in your .env file or Cloud Run configuration.
        """
        # Configure the Google AI library with our API key
        # This key authenticates us with Google's AI services
        genai.configure(api_key=settings.google_api_key)
        
        # The model name - using Gemini 2.0 Flash for:
        # - Fast response times (important for real-time chat)
        # - Emotional tone detection (understands user's mood)
        # - Cost efficiency (flash models are cheaper)
        self.model_name = "gemini-2.0-flash"
        
        # EVA's personality and behavior instructions
        # This tells the AI how to behave in conversations
        # Think of it like giving an actor their character description
        self.system_instruction = """
        You are EVA, a personal AI assistant inspired by JARVIS and Baymax.
        
        YOUR PERSONALITY:
        - Warm, friendly, and approachable (like Baymax)
        - Intelligent and capable (like JARVIS)
        - Concise but helpful - don't be overly verbose
        - Use a conversational tone, not robotic
        
        YOUR CAPABILITIES:
        - You can help with questions, tasks, and conversation
        - You remember context within a conversation
        - You can detect emotional tone and respond appropriately
        
        GUIDELINES:
        - Keep responses concise unless the user asks for detail
        - Be proactive in offering help when appropriate
        - If you don't know something, say so honestly
        - Never pretend to have capabilities you don't have
        
        RESPONSE STYLE:
        - For simple questions: 1-2 sentences
        - For explanations: Use bullet points or numbered lists
        - For emotional support: Be empathetic and understanding
        """
        
        # Create the Gemini model instance
        # This is the actual AI we'll be talking to
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.system_instruction
        )
        
        # Store for active chat sessions
        # Key: user_id, Value: chat session object
        # This allows us to maintain conversation history per user
        self._chat_sessions: Dict[str, Any] = {}
    
    def _get_or_create_chat(self, user_id: str, conversation_id: Optional[str] = None):
        """
        Get an existing chat session or create a new one.
        
        WHAT THIS DOES:
            Each user can have multiple conversations. This method:
            1. Checks if a chat session already exists for this user+conversation
            2. If yes, returns it (so the AI remembers the conversation history)
            3. If no, creates a new one
        
        PARAMETERS:
            user_id (str): The unique identifier for the user
            conversation_id (str, optional): Specific conversation ID
                                            If None, uses "default"
        
        RETURNS:
            A chat session object that maintains conversation history
        
        WHY THIS MATTERS:
            Without this, the AI would forget everything between messages.
            With this, it can say things like "As I mentioned earlier..."
        """
        # Create a unique key for this user's conversation
        session_key = f"{user_id}:{conversation_id or 'default'}"
        
        # Check if we already have a chat session for this key
        if session_key not in self._chat_sessions:
            # No existing session - create a new one
            # start_chat() creates a new conversation with empty history
            self._chat_sessions[session_key] = self.model.start_chat(history=[])
        
        return self._chat_sessions[session_key]
    
    async def send_message(
        self, 
        message: str, 
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Send a message to EVA and get a response.
        
        THIS IS THE MAIN METHOD - Used for regular text chat.
        
        PARAMETERS:
            message (str): What the user said (e.g., "What's the weather?")
            user_id (str): Who is asking (e.g., "user_abc123")
            conversation_id (str, optional): Which conversation this belongs to
        
        RETURNS:
            str: EVA's response text
        
        EXAMPLE:
            response = await gemini_service.send_message(
                message="Hello EVA!",
                user_id="user123"
            )
            # response = "Hello! I'm EVA, your personal assistant. How can I help?"
        
        ERROR HANDLING:
            If something goes wrong (API error, network issue), this catches
            the error and returns a friendly error message instead of crashing.
        """
        try:
            # Get the chat session for this user
            # This maintains conversation history
            chat = self._get_or_create_chat(user_id, conversation_id)
            
            # Send the message to Gemini and wait for response
            # send_message_async is non-blocking (good for performance)
            response = await chat.send_message_async(message)
            
            # Extract and return the text from the response
            return response.text
            
        except Exception as e:
            # Log the error for debugging
            print(f"Gemini API Error: {str(e)}")
            
            # Return a friendly error message to the user
            # Don't expose technical details to end users
            return "I'm sorry, I encountered an issue processing your request. Please try again."
    
    async def send_message_stream(
        self, 
        message: str, 
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response in real-time.
        
        THIS IS FOR VOICE CALLS - Streams words as they're generated.
        
        WHAT IS STREAMING?
            Instead of waiting for the complete response, we get words
            as the AI generates them. This is like:
            - Normal: Wait 3 seconds, then get "Hello, how are you today?"
            - Streaming: Get "Hello," then ", how" then " are you" then " today?"
        
        WHY USE STREAMING?
            For voice calls, we want to speak as soon as possible.
            Streaming lets us start speaking before the AI finishes thinking.
        
        PARAMETERS:
            message (str): What the user said
            user_id (str): Who is asking  
            conversation_id (str, optional): Which conversation
        
        YIELDS:
            str: Chunks of text as they're generated
        
        EXAMPLE:
            async for chunk in gemini_service.send_message_stream("Tell me a story", "user123"):
                print(chunk, end="")  # Prints each word as it arrives
        """
        try:
            # Get the chat session
            chat = self._get_or_create_chat(user_id, conversation_id)
            
            # Send message and get streaming response
            response = await chat.send_message_async(message, stream=True)
            
            # Yield each chunk as it arrives
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"Gemini Streaming Error: {str(e)}")
            yield "I'm sorry, I encountered an issue. Please try again."
    
    def clear_conversation(self, user_id: str, conversation_id: Optional[str] = None):
        """
        Clear a user's conversation history.
        
        WHEN TO USE:
            - User starts a "New Chat" 
            - User explicitly asks to "forget" the conversation
            - Conversation gets too long (memory management)
        
        PARAMETERS:
            user_id (str): The user whose conversation to clear
            conversation_id (str, optional): Specific conversation to clear
        
        WHAT HAPPENS:
            The chat session is deleted. Next message will start fresh
            with no memory of previous messages.
        """
        session_key = f"{user_id}:{conversation_id or 'default'}"
        
        if session_key in self._chat_sessions:
            del self._chat_sessions[session_key]
    
    def get_active_conversations(self, user_id: str) -> List[str]:
        """
        Get list of active conversation IDs for a user.
        
        RETURNS:
            List of conversation IDs that have active chat sessions
        
        EXAMPLE:
            conversations = gemini_service.get_active_conversations("user123")
            # conversations = ["default", "work-chat", "personal-chat"]
        """
        prefix = f"{user_id}:"
        return [
            key.replace(prefix, "") 
            for key in self._chat_sessions.keys() 
            if key.startswith(prefix)
        ]


# Create a singleton instance
# This means the entire application shares one GeminiService
# Benefits: Efficient memory use, shared conversation state
gemini_service = GeminiService()
