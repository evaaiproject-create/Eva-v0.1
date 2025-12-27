"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "uid": "test_user_123",
        "email": "test@example.com",
        "display_name": "Test User",
        "devices": ["device_001"]
    }


@pytest.fixture
def sample_message():
    """Sample conversation message."""
    return {
        "role": "user",
        "content": "Hello, Eva!"
    }


@pytest.fixture
def sample_memory():
    """Sample memory data."""
    return {
        "category": "preference",
        "content": "User prefers dark mode",
        "importance": 7
    }


@pytest.fixture
def sample_audio_base64():
    """Sample base64 audio data (empty placeholder)."""
    # This is a minimal valid WAV header for testing
    import base64
    # Minimal WAV file header (44 bytes)
    wav_header = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Subchunk1 size (16)
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Num channels (1)
        0x80, 0x3E, 0x00, 0x00,  # Sample rate (16000)
        0x00, 0x7D, 0x00, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample (16)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00   # Data size (0)
    ])
    return base64.b64encode(wav_header).decode('utf-8')
