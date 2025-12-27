"""
Text-to-Speech (TTS) service for Eva.
Provides modular TTS engine support with Google Cloud TTS and custom engine support.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import base64

from app.config import settings


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice name/ID (engine-specific)
            language: Language code
            
        Returns:
            Dictionary with synthesis result:
            {
                "audio": bytes,  # Raw audio bytes
                "audio_base64": str,  # Base64 encoded audio
                "content_type": str,  # e.g., "audio/mp3"
                "duration_seconds": float
            }
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the engine name."""
        pass
    
    @abstractmethod
    def list_voices(self, language: str = "en-US") -> list:
        """List available voices for the given language."""
        pass


class GoogleTTSEngine(TTSEngine):
    """
    Google Cloud Text-to-Speech engine.
    Provides high-quality neural voices.
    """
    
    def __init__(self):
        """Initialize Google Cloud TTS client."""
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Google Cloud TTS client."""
        if self._client is None:
            try:
                from google.cloud import texttospeech
                self._client = texttospeech.TextToSpeechClient()
            except ImportError:
                raise ImportError("google-cloud-texttospeech not installed. Run: pip install google-cloud-texttospeech")
        return self._client
    
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Synthesize text using Google Cloud TTS.
        
        Args:
            text: Text to convert
            voice: Voice name (e.g., "en-US-Neural2-C")
            language: Language code
            
        Returns:
            Synthesis result dictionary with audio
        """
        try:
            from google.cloud import texttospeech
            
            client = self._get_client()
            
            # Set up input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=voice if voice else f"{language}-Neural2-C",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform synthesis
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            audio_content = response.audio_content
            audio_base64 = base64.b64encode(audio_content).decode("utf-8")
            
            # Estimate duration (rough estimate based on text length)
            duration_estimate = len(text.split()) * 0.4  # ~0.4 seconds per word
            
            return {
                "audio": audio_content,
                "audio_base64": audio_base64,
                "content_type": "audio/mp3",
                "duration_seconds": duration_estimate,
                "engine": "google"
            }
            
        except Exception as e:
            return {
                "audio": b"",
                "audio_base64": "",
                "content_type": "audio/mp3",
                "duration_seconds": 0.0,
                "engine": "google",
                "error": str(e)
            }
    
    def get_name(self) -> str:
        return "google"
    
    def list_voices(self, language: str = "en-US") -> list:
        """
        List available voices from Google Cloud TTS.
        
        Args:
            language: Language code to filter voices
            
        Returns:
            List of voice dictionaries
        """
        try:
            from google.cloud import texttospeech
            
            client = self._get_client()
            response = client.list_voices(language_code=language)
            
            voices = []
            for voice in response.voices:
                voices.append({
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                    "natural_sample_rate": voice.natural_sample_rate_hertz
                })
            
            return voices
            
        except Exception as e:
            return [{"error": str(e)}]


class CustomTTSEngine(TTSEngine):
    """
    Placeholder for custom TTS engine integration.
    Can be extended to support Coqui TTS or other engines.
    """
    
    def __init__(self):
        """Initialize custom TTS engine."""
        pass
    
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Synthesize text using custom TTS.
        
        This is a placeholder that should be implemented
        when integrating a specific custom TTS engine.
        """
        return {
            "audio": b"",
            "audio_base64": "",
            "content_type": "audio/wav",
            "duration_seconds": 0.0,
            "engine": "custom",
            "error": "Custom TTS engine not configured. Please implement CustomTTSEngine."
        }
    
    def get_name(self) -> str:
        return "custom"
    
    def list_voices(self, language: str = "en-US") -> list:
        """List available voices for custom engine."""
        return [
            {
                "name": "default",
                "language_codes": [language],
                "note": "Custom engine placeholder"
            }
        ]


class TTSService:
    """
    Main TTS service that provides a unified interface to different TTS engines.
    
    Usage:
        tts = TTSService()
        result = await tts.synthesize("Hello, world!")
    """
    
    def __init__(self):
        """Initialize TTS service with configured engine."""
        self._engines: Dict[str, TTSEngine] = {}
        
        # Register available engines
        self._engines["google"] = GoogleTTSEngine()
        self._engines["custom"] = CustomTTSEngine()
    
    def get_engine(self, engine_name: Optional[str] = None) -> TTSEngine:
        """
        Get a TTS engine by name.
        
        Args:
            engine_name: Engine name (google, custom). Defaults to configured engine.
            
        Returns:
            TTSEngine instance
        """
        if engine_name is None:
            engine_name = settings.tts_engine
        
        if engine_name not in self._engines:
            raise ValueError(f"Unknown TTS engine: {engine_name}")
        
        return self._engines[engine_name]
    
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: str = "en-US",
        engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech using the configured engine.
        
        Args:
            text: Text to convert to speech
            voice: Voice name/ID
            language: Language code
            engine: Optional engine override
            
        Returns:
            Synthesis result dictionary with audio
        """
        tts_engine = self.get_engine(engine)
        return await tts_engine.synthesize(text, voice, language)
    
    def list_engines(self) -> list:
        """List available TTS engines."""
        return list(self._engines.keys())
    
    def list_voices(self, language: str = "en-US", engine: Optional[str] = None) -> list:
        """
        List available voices for the specified engine.
        
        Args:
            language: Language code
            engine: Engine name (defaults to configured engine)
            
        Returns:
            List of voice dictionaries
        """
        tts_engine = self.get_engine(engine)
        return tts_engine.list_voices(language)
    
    def get_current_engine(self) -> str:
        """Get the currently configured engine name."""
        return settings.tts_engine


# Global TTS service instance
tts_service = TTSService()
