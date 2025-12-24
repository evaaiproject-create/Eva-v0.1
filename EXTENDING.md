# Extending Eva - Developer Guide

This guide shows you how to extend Eva with new capabilities by adding custom functions.

## Overview

Eva's function calling framework allows you to easily add new features without modifying core code. Functions are registered in the `FunctionRegistry` and can be called via the API.

## Adding a New Function

### Step 1: Define Your Function

Create a new file or add to an existing one. For organization, you can create a new module:

```python
# app/services/custom_functions.py

from typing import Dict, Any
import requests

def get_weather(city: str, country_code: str = "US") -> Dict[str, Any]:
    """
    Get current weather for a city.
    
    Args:
        city: City name (e.g., "San Francisco")
        country_code: Two-letter country code (default: "US")
    
    Returns:
        Dictionary with weather information
    """
    # Example using a free weather API
    # In production, you'd use a real API key
    api_key = "YOUR_WEATHER_API_KEY"
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{country_code}",
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }
    except Exception as e:
        raise ValueError(f"Failed to get weather: {str(e)}")
```

### Step 2: Register Your Function

Register it in the `FunctionRegistry`. Edit `app/services/function_service.py`:

```python
# In function_service.py

from app.services.custom_functions import get_weather

class FunctionRegistry:
    # ... existing code ...
    
    def _register_builtin_functions(self):
        """Register built-in functions that are always available."""
        
        # ... existing functions ...
        
        # Register weather function
        self.register(
            name="get_weather",
            func=get_weather,
            description="Get current weather for a city",
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Two-letter country code",
                        "default": "US"
                    }
                },
                "required": ["city"]
            }
        )
```

### Step 3: Test Your Function

```python
# test_custom_function.py

from app.services.function_service import function_registry
from app.models import FunctionCall

# Test the function
async def test():
    function_call = FunctionCall(
        function_name="get_weather",
        parameters={"city": "San Francisco"},
        user_id="test_user"
    )
    
    result = await function_registry.call(function_call)
    print(result)

# Run test
import asyncio
asyncio.run(test())
```

### Step 4: Use via API

```bash
curl -X POST "http://localhost:8000/functions/call" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_weather",
    "parameters": {
      "city": "San Francisco",
      "country_code": "US"
    }
  }'
```

## Advanced Examples

### Async Function

For I/O-bound operations, use async:

```python
import asyncio
import httpx

async def async_web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Perform web search asynchronously.
    
    Args:
        query: Search query
        num_results: Number of results to return
    
    Returns:
        Search results
    """
    async with httpx.AsyncClient() as client:
        # Use a search API
        response = await client.get(
            "https://api.searchprovider.com/search",
            params={"q": query, "limit": num_results}
        )
        return response.json()

# Register it
function_registry.register(
    name="web_search",
    func=async_web_search,
    description="Search the web for information",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }
)
```

### Function with Dependencies

Use dependency injection for services:

```python
from app.services.firestore_service import firestore_service

async def save_note(title: str, content: str, user_id: str) -> Dict[str, Any]:
    """
    Save a note to user's storage.
    
    Args:
        title: Note title
        content: Note content
        user_id: User identifier
    
    Returns:
        Saved note information
    """
    note_data = {
        "title": title,
        "content": content,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }
    
    # Save to Firestore
    doc_ref = firestore_service.db.collection("notes").add(note_data)
    note_id = doc_ref[1].id
    
    return {
        "note_id": note_id,
        "title": title,
        "message": "Note saved successfully"
    }
```

### Function with Error Handling

Always include proper error handling:

```python
def calculate_advanced(expression: str) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression (e.g., "2 + 2 * 3")
    
    Returns:
        Calculation result
    """
    import ast
    import operator
    
    # Safe operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }
    
    def eval_expr(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_expr(node.left),
                eval_expr(node.right)
            )
        else:
            raise ValueError("Unsupported operation")
    
    try:
        tree = ast.parse(expression, mode='eval')
        result = eval_expr(tree.body)
        return {"result": result, "expression": expression}
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")
```

## Function Categories

Organize functions by category:

### 1. Information Retrieval
- Weather
- News
- Web search
- Knowledge base queries

### 2. Communication
- Send email
- Send SMS
- Schedule messages
- Create reminders

### 3. Productivity
- Create calendar events
- Manage tasks
- Take notes
- Set timers/alarms

### 4. Smart Home (if integrated)
- Control lights
- Adjust thermostat
- Check security cameras
- Lock/unlock doors

### 5. Entertainment
- Play music
- Find movies
- Tell jokes
- Play games

### 6. Data Analysis
- Analyze data
- Generate charts
- Run calculations
- Process files

## Best Practices

### 1. Function Design

```python
def good_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Clear description of what the function does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 10)
    
    Returns:
        Dictionary with clear structure
    
    Raises:
        ValueError: When input is invalid
    """
    # Validate inputs
    if not param1:
        raise ValueError("param1 is required")
    
    # Do work
    result = process(param1, param2)
    
    # Return structured data
    return {
        "success": True,
        "data": result,
        "metadata": {"processed_at": datetime.utcnow()}
    }
```

### 2. Error Handling

Always raise descriptive errors:

```python
try:
    result = api_call()
except ConnectionError:
    raise ValueError("Cannot connect to external service")
except Timeout:
    raise ValueError("Request timed out")
except Exception as e:
    raise ValueError(f"Unexpected error: {str(e)}")
```

### 3. Logging

Add logging for debugging:

```python
import logging

logger = logging.getLogger(__name__)

def my_function(param: str) -> Dict[str, Any]:
    logger.info(f"my_function called with param: {param}")
    
    try:
        result = process(param)
        logger.debug(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in my_function: {e}")
        raise
```

### 4. Testing

Create tests for your functions:

```python
# tests/test_custom_functions.py

import pytest
from app.services.custom_functions import get_weather

def test_get_weather():
    result = get_weather("San Francisco", "US")
    assert "temperature" in result
    assert "city" in result
    assert result["city"] == "San Francisco"

def test_get_weather_invalid_city():
    with pytest.raises(ValueError):
        get_weather("InvalidCity123", "ZZ")
```

### 5. Documentation

Document your functions in the schema:

```python
function_registry.register(
    name="my_function",
    func=my_function,
    description="Detailed description of what this does and when to use it",
    parameters_schema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Detailed description of param1"
            }
        },
        "required": ["param1"]
    }
)
```

## Real-World Examples

### Email Function

```python
import smtplib
from email.mime.text import MIMEText

async def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Send an email."""
    # Use environment variables for credentials
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to
    
    try:
        with smtplib.SMTP(smtp_server, 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return {"success": True, "message": "Email sent"}
    except Exception as e:
        raise ValueError(f"Failed to send email: {str(e)}")
```

### Calendar Function

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = ""
) -> Dict[str, Any]:
    """Create a Google Calendar event."""
    # Assumes user has authorized Google Calendar access
    creds = get_user_credentials()  # Implement this
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': title,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return {"event_id": event['id'], "link": event['htmlLink']}
```

## Performance Tips

1. **Cache results** for expensive operations
2. **Use async** for I/O operations
3. **Batch operations** when possible
4. **Set timeouts** for external API calls
5. **Rate limit** expensive operations

## Security Considerations

1. **Validate all inputs** before processing
2. **Sanitize user data** before storing
3. **Use environment variables** for secrets
4. **Rate limit** function calls per user
5. **Audit logs** for sensitive operations

## Next Steps

1. Browse existing functions in `app/services/function_service.py`
2. Identify capabilities you want to add
3. Implement your functions following the patterns above
4. Test thoroughly
5. Submit a pull request or keep for your deployment

---

For questions or examples, see the main README.md or open an issue on GitHub.
