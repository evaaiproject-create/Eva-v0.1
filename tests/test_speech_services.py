"""
Unit tests for speech services (STT and TTS).
Tests service interfaces and engine selection.
"""
import pytest

from app.services.stt_service import STTService, WhisperSTTEngine, GoogleSTTEngine
from app.services.tts_service import TTSService, GoogleTTSEngine, CustomTTSEngine


class TestSTTService:
    """Tests for STTService class."""
    
    @pytest.fixture
    def service(self):
        """Create an STT service instance."""
        return STTService()
    
    def test_service_initialization(self, service):
        """Test that service initializes with available engines."""
        engines = service.list_engines()
        
        assert "whisper" in engines
        assert "google" in engines
    
    def test_get_engine_whisper(self, service):
        """Test getting whisper engine."""
        engine = service.get_engine("whisper")
        
        assert engine is not None
        assert isinstance(engine, WhisperSTTEngine)
        assert engine.get_name() == "whisper"
    
    def test_get_engine_google(self, service):
        """Test getting Google STT engine."""
        engine = service.get_engine("google")
        
        assert engine is not None
        assert isinstance(engine, GoogleSTTEngine)
        assert engine.get_name() == "google"
    
    def test_get_engine_invalid(self, service):
        """Test getting invalid engine raises error."""
        with pytest.raises(ValueError, match="Unknown STT engine"):
            service.get_engine("invalid_engine")
    
    def test_get_current_engine(self, service):
        """Test getting current configured engine."""
        current = service.get_current_engine()
        
        assert current in ["whisper", "google"]


class TestTTSService:
    """Tests for TTSService class."""
    
    @pytest.fixture
    def service(self):
        """Create a TTS service instance."""
        return TTSService()
    
    def test_service_initialization(self, service):
        """Test that service initializes with available engines."""
        engines = service.list_engines()
        
        assert "google" in engines
        assert "custom" in engines
    
    def test_get_engine_google(self, service):
        """Test getting Google TTS engine."""
        engine = service.get_engine("google")
        
        assert engine is not None
        assert isinstance(engine, GoogleTTSEngine)
        assert engine.get_name() == "google"
    
    def test_get_engine_custom(self, service):
        """Test getting custom TTS engine."""
        engine = service.get_engine("custom")
        
        assert engine is not None
        assert isinstance(engine, CustomTTSEngine)
        assert engine.get_name() == "custom"
    
    def test_get_engine_invalid(self, service):
        """Test getting invalid engine raises error."""
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            service.get_engine("invalid_engine")
    
    def test_get_current_engine(self, service):
        """Test getting current configured engine."""
        current = service.get_current_engine()
        
        assert current in ["google", "custom"]


class TestWhisperSTTEngine:
    """Tests for WhisperSTTEngine class."""
    
    def test_engine_name(self):
        """Test engine name."""
        engine = WhisperSTTEngine()
        assert engine.get_name() == "whisper"


class TestGoogleSTTEngine:
    """Tests for GoogleSTTEngine class."""
    
    def test_engine_name(self):
        """Test engine name."""
        engine = GoogleSTTEngine()
        assert engine.get_name() == "google"


class TestGoogleTTSEngine:
    """Tests for GoogleTTSEngine class."""
    
    def test_engine_name(self):
        """Test engine name."""
        engine = GoogleTTSEngine()
        assert engine.get_name() == "google"


class TestCustomTTSEngine:
    """Tests for CustomTTSEngine class."""
    
    def test_engine_name(self):
        """Test engine name."""
        engine = CustomTTSEngine()
        assert engine.get_name() == "custom"
    
    def test_list_voices(self):
        """Test listing voices returns placeholder."""
        engine = CustomTTSEngine()
        voices = engine.list_voices("en-US")
        
        assert len(voices) > 0
        assert voices[0]["name"] == "default"
