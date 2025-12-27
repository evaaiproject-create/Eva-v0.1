"""
Unit tests for the conversation service.
Tests intent analysis and conversation state management.
"""
import pytest

from app.services.conversation_service import ConversationService


class TestConversationService:
    """Tests for ConversationService class."""
    
    @pytest.fixture
    def service(self):
        """Create a conversation service instance."""
        return ConversationService()
    
    @pytest.mark.asyncio
    async def test_analyze_intent_acknowledgment(self, service):
        """Test detecting acknowledgment intents."""
        # Test various acknowledgments
        acknowledgments = ["okay", "ok", "yeah", "yes", "no", "got it", "sure"]
        
        for ack in acknowledgments:
            result = await service.analyze_intent(ack)
            assert result["is_acknowledgment"] is True
            assert result["type"] == "acknowledgment"
    
    @pytest.mark.asyncio
    async def test_analyze_intent_command(self, service):
        """Test detecting command intents."""
        commands = [
            "set a reminder for tomorrow",
            "create a new note",
            "add this to my list",
            "delete the last message",
            "show my calendar",
            "list all tasks"
        ]
        
        for cmd in commands:
            result = await service.analyze_intent(cmd)
            assert result["is_command"] is True
            assert result["type"] == "command"
    
    @pytest.mark.asyncio
    async def test_analyze_intent_interruption(self, service):
        """Test detecting interruption intents."""
        interruptions = [
            "stop",
            "wait a moment",
            "hold on",
            "pause that",
            "cancel",
            "never mind"
        ]
        
        for interrupt in interruptions:
            result = await service.analyze_intent(interrupt)
            assert result["is_interruption"] is True
            assert result["type"] == "interruption"
    
    @pytest.mark.asyncio
    async def test_analyze_intent_conversation(self, service):
        """Test regular conversation messages."""
        messages = [
            "What's the weather like today?",
            "Tell me about quantum computing",
            "How are you doing?",
            "I need help with my project"
        ]
        
        for msg in messages:
            result = await service.analyze_intent(msg)
            assert result["type"] == "conversation"
            assert result["is_acknowledgment"] is False
            assert result["is_command"] is False
            assert result["is_interruption"] is False
    
    @pytest.mark.asyncio
    async def test_analyze_intent_confidence(self, service):
        """Test that confidence scores are reasonable."""
        result = await service.analyze_intent("okay")
        assert 0.0 <= result["confidence"] <= 1.0
        
        result = await service.analyze_intent("Hello there!")
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_default_system_prompt(self, service):
        """Test that default system prompt is set."""
        assert service.DEFAULT_SYSTEM_PROMPT is not None
        assert "Eva" in service.DEFAULT_SYSTEM_PROMPT
        assert len(service.DEFAULT_SYSTEM_PROMPT) > 100


class TestConversationServiceModels:
    """Tests for conversation-related Pydantic models."""
    
    def test_chat_request_model(self):
        """Test importing and using ChatRequest model."""
        # Import here to avoid circular imports
        from app.api.conversation import ChatRequest
        
        request = ChatRequest(
            message="Hello Eva",
            session_id="session_123",
            temperature=0.5
        )
        
        assert request.message == "Hello Eva"
        assert request.session_id == "session_123"
        assert request.temperature == 0.5
        assert request.include_memory is True  # Default
        assert request.model == "gpt-3.5-turbo"  # Default
    
    def test_chat_response_model(self):
        """Test ChatResponse model."""
        from app.api.conversation import ChatResponse
        
        response = ChatResponse(
            success=True,
            message="Hello! How can I help you?"
        )
        
        assert response.success is True
        assert response.message == "Hello! How can I help you?"
        assert response.error is None
    
    def test_intent_analysis_model(self):
        """Test IntentAnalysis model."""
        from app.api.conversation import IntentAnalysis
        
        intent = IntentAnalysis(
            type="command",
            is_acknowledgment=False,
            is_command=True,
            is_interruption=False,
            confidence=0.85
        )
        
        assert intent.type == "command"
        assert intent.is_command is True
        assert intent.confidence == 0.85
