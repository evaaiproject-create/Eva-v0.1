"""
Unit tests for the function service.
Tests the function registry and function calling framework.
"""
import pytest
from datetime import datetime

from app.services.function_service import FunctionRegistry
from app.models import FunctionCall, FunctionResponse


class TestFunctionRegistry:
    """Tests for FunctionRegistry class."""
    
    def test_registry_initialization(self):
        """Test that registry initializes with built-in functions."""
        registry = FunctionRegistry()
        
        functions = registry.list_functions()
        assert "echo" in functions
        assert "get_time" in functions
        assert "calculate" in functions
    
    def test_register_function(self):
        """Test registering a new function."""
        registry = FunctionRegistry()
        
        def custom_func(param: str) -> dict:
            return {"result": param}
        
        registry.register(
            name="custom_test",
            func=custom_func,
            description="Test function",
            parameters_schema={"type": "object"}
        )
        
        functions = registry.list_functions()
        assert "custom_test" in functions
        assert functions["custom_test"]["description"] == "Test function"
    
    def test_get_function(self):
        """Test getting a registered function."""
        registry = FunctionRegistry()
        
        func = registry.get_function("echo")
        assert func is not None
        assert callable(func)
        
        # Test non-existent function
        func = registry.get_function("nonexistent")
        assert func is None
    
    @pytest.mark.asyncio
    async def test_call_echo_function(self):
        """Test calling the echo function."""
        registry = FunctionRegistry()
        
        call = FunctionCall(
            function_name="echo",
            parameters={"message": "Hello, World!"},
            user_id="test_user"
        )
        
        # Note: This would need mocking of firestore_service for actual test
        # For now, we test the function directly
        func = registry.get_function("echo")
        result = func(message="Hello, World!")
        
        assert result["echo"] == "Hello, World!"
    
    def test_calculate_function_add(self):
        """Test calculate function with addition."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        result = func(operation="add", a=5, b=3)
        
        assert result["result"] == 8
    
    def test_calculate_function_subtract(self):
        """Test calculate function with subtraction."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        result = func(operation="subtract", a=10, b=4)
        
        assert result["result"] == 6
    
    def test_calculate_function_multiply(self):
        """Test calculate function with multiplication."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        result = func(operation="multiply", a=6, b=7)
        
        assert result["result"] == 42
    
    def test_calculate_function_divide(self):
        """Test calculate function with division."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        result = func(operation="divide", a=20, b=4)
        
        assert result["result"] == 5
    
    def test_calculate_function_divide_by_zero(self):
        """Test calculate function handles division by zero."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        
        with pytest.raises(ValueError, match="Division by zero"):
            func(operation="divide", a=10, b=0)
    
    def test_calculate_function_invalid_operation(self):
        """Test calculate function with invalid operation."""
        registry = FunctionRegistry()
        
        func = registry.get_function("calculate")
        
        with pytest.raises(ValueError, match="Unknown operation"):
            func(operation="power", a=2, b=3)
    
    def test_get_time_function(self):
        """Test get_time function returns current time."""
        registry = FunctionRegistry()
        
        func = registry.get_function("get_time")
        result = func()
        
        assert "timestamp" in result
        assert "formatted" in result
        assert "UTC" in result["formatted"]
    
    def test_list_functions_metadata(self):
        """Test that function metadata is complete."""
        registry = FunctionRegistry()
        
        functions = registry.list_functions()
        
        for name, metadata in functions.items():
            assert "description" in metadata
            assert "parameters_schema" in metadata
            assert "registered_at" in metadata
            assert isinstance(metadata["registered_at"], datetime)


class TestFunctionCall:
    """Tests for FunctionCall model."""
    
    def test_function_call_creation(self):
        """Test creating a FunctionCall object."""
        call = FunctionCall(
            function_name="echo",
            parameters={"message": "test"},
            user_id="user_123",
            device_id="device_001"
        )
        
        assert call.function_name == "echo"
        assert call.parameters == {"message": "test"}
        assert call.user_id == "user_123"
        assert call.device_id == "device_001"
    
    def test_function_call_defaults(self):
        """Test FunctionCall default values."""
        call = FunctionCall(
            function_name="test",
            user_id="user_123"
        )
        
        assert call.parameters == {}
        assert call.device_id is None
        assert call.timestamp is not None


class TestFunctionResponse:
    """Tests for FunctionResponse model."""
    
    def test_success_response(self):
        """Test successful function response."""
        response = FunctionResponse(
            success=True,
            result={"value": 42},
            execution_time=0.001
        )
        
        assert response.success is True
        assert response.result == {"value": 42}
        assert response.error is None
        assert response.execution_time == 0.001
    
    def test_error_response(self):
        """Test error function response."""
        response = FunctionResponse(
            success=False,
            error="Function not found",
            execution_time=0.0
        )
        
        assert response.success is False
        assert response.result is None
        assert response.error == "Function not found"
