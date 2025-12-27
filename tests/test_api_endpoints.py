"""
End-to-end tests for API endpoints.
Uses FastAPI TestClient to test the REST API.
"""
import pytest
from fastapi.testclient import TestClient

from main import app


class TestRootEndpoints:
    """Tests for root and health endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Eva Backend API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"
        assert "documentation" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "max_users" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_verify_token_invalid(self, client):
        """Test verifying invalid token."""
        response = client.get("/auth/verify?token=invalid_token")
        
        assert response.status_code == 200
        data = response.json()
        
        # Invalid token should return valid: false
        assert data["valid"] is False


class TestWebSocketInfo:
    """Tests for WebSocket info endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_websocket_info_endpoint(self, client):
        """Test WebSocket info endpoint."""
        response = client.get("/ws/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoint" in data
        assert "protocol" in data
        assert "client_to_server" in data["protocol"]
        assert "server_to_client" in data["protocol"]
        assert "example_messages" in data


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Eva Backend API"
    
    def test_swagger_ui(self, client):
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc(self, client):
        """Test ReDoc is accessible."""
        response = client.get("/redoc")
        
        assert response.status_code == 200


class TestProtectedEndpointsWithoutAuth:
    """Tests for protected endpoints without authentication."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_users_me_requires_auth(self, client):
        """Test /users/me requires authentication."""
        response = client.get("/users/me")
        
        # Should return 403 Forbidden (no auth header)
        assert response.status_code == 403
    
    def test_sessions_requires_auth(self, client):
        """Test /sessions requires authentication."""
        response = client.get("/sessions")
        
        assert response.status_code == 403
    
    def test_functions_requires_auth(self, client):
        """Test /functions requires authentication."""
        response = client.get("/functions")
        
        assert response.status_code == 403
    
    def test_conversation_chat_requires_auth(self, client):
        """Test /conversation/chat requires authentication."""
        response = client.post(
            "/conversation/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 403
    
    def test_memory_requires_auth(self, client):
        """Test /memory requires authentication."""
        response = client.get("/memory")
        
        assert response.status_code == 403
    
    def test_speech_transcribe_requires_auth(self, client):
        """Test /speech/transcribe requires authentication."""
        response = client.post(
            "/speech/transcribe/base64",
            json={"audio_base64": "dGVzdA==", "language": "en-US"}
        )
        
        assert response.status_code == 403 or response.status_code == 422


class TestInputValidation:
    """Tests for request input validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_register_missing_id_token(self, client):
        """Test registration fails without id_token."""
        response = client.post(
            "/auth/register",
            json={}
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_login_missing_id_token(self, client):
        """Test login fails without id_token."""
        response = client.post(
            "/auth/login",
            json={}
        )
        
        assert response.status_code == 422
