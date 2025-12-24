# Quick Start Guide

Get Eva up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud account (free tier available)

## Installation (5 minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/evaaiproject-create/Eva-v0.1.git
cd Eva-v0.1

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_installation.py
```

You should see: ✅ All tests passed!

### 2. Google Cloud Setup (10 minutes)

Follow the detailed guide: [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)

Quick version:
1. Create Google Cloud project
2. Enable Firestore API
3. Create service account → download JSON key
4. Create OAuth 2.0 credentials
5. Save service account key as `service-account-key.json`

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

Update these values:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
API_SECRET_KEY=generate-with-openssl-rand-hex-32
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Start the Server

```bash
# Start Eva
python main.py

# Or with auto-reload for development
uvicorn main:app --reload
```

You should see:
```
🤖 Eva Backend Starting...
```

### 5. Test the API

Open your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **API Info**: http://localhost:8000

## Your First API Call

### Option 1: Using the Interactive Docs

1. Go to http://localhost:8000/docs
2. Scroll to "Authentication" section
3. Try the `/health` endpoint (no auth needed)
4. Click "Try it out" → "Execute"

### Option 2: Using curl

```bash
# Health check
curl http://localhost:8000/health

# Response:
# {"status":"healthy","environment":"development","max_users":5}
```

### Option 3: Using Python Client

```python
# examples/quick_test.py
from examples.python_client import EvaClient

client = EvaClient("http://localhost:8000")

# Check health
import requests
health = requests.get("http://localhost:8000/health").json()
print(f"Eva is {health['status']}!")

# After authentication, you can:
# client.call_function("calculate", {"operation": "add", "a": 5, "b": 3})
```

## Next Steps

### 1. Authenticate Users

To use authenticated endpoints, you need to:

1. **Set up Google OAuth** on your frontend
2. **Get a Google ID token** from the OAuth flow
3. **Register or login** a user:

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN",
    "device_id": "my_device"
  }'
```

4. **Use the access token** in subsequent requests:

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Try Built-in Functions

```bash
# List available functions
curl "http://localhost:8000/functions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Call the calculate function
curl -X POST "http://localhost:8000/functions/call?function_name=calculate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation": "add", "a": 10, "b": 5}'

# Response:
# {"success":true,"result":{"result":15},"execution_time":0.001}
```

### 3. Create a Session (Cross-Device Sync)

```bash
curl -X POST "http://localhost:8000/sessions?device_id=my_device" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"app_state": "active", "data": {}}'
```

### 4. Extend Eva

Add custom functions - see [EXTENDING.md](EXTENDING.md)

Example:
```python
# Add to app/services/function_service.py

def greet_user(name: str) -> dict:
    """Greet a user by name."""
    return {"message": f"Hello, {name}!"}

# Register it
function_registry.register(
    name="greet_user",
    func=greet_user,
    description="Greet a user",
    parameters_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
)
```

## Troubleshooting

### Port 8000 Already in Use

```bash
# Use a different port
uvicorn main:app --host 0.0.0.0 --port 8080
```

### "Could not determine credentials"

- Check that `service-account-key.json` exists
- Verify `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
- Try absolute path: `/full/path/to/service-account-key.json`

### "Invalid Google ID token"

- Verify `GOOGLE_CLIENT_ID` matches your OAuth client
- Token may have expired - generate a new one
- Check that OAuth consent screen is configured

### Packages Not Installing

```bash
# Upgrade pip
pip install --upgrade pip

# Try installing individually
pip install fastapi uvicorn google-cloud-firestore
```

## Development Tips

### Auto-reload on Code Changes

```bash
uvicorn main:app --reload
```

### View Logs

The server prints logs to stdout. Look for:
- `INFO` - Normal operations
- `WARNING` - Potential issues
- `ERROR` - Problems that need attention

### Debug Mode

Set in `.env`:
```env
ENVIRONMENT=development
```

This enables:
- Detailed error messages
- Auto-reload
- CORS for localhost

### Test Without Frontend

Use the interactive API docs at `/docs` to:
- See all endpoints
- Test requests
- View response schemas
- No frontend needed!

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Google Cloud Run
- Heroku
- AWS
- Docker

Quick production checklist:
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `API_SECRET_KEY`
- [ ] Configure CORS for your domain
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure backups

## Resources

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Extension Guide**: [EXTENDING.md](EXTENDING.md)
- **Google Cloud Setup**: [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)
- **Full Documentation**: [README.md](README.md)

## Getting Help

1. Check the troubleshooting sections
2. Review the documentation
3. Check example code in `examples/`
4. Open an issue on GitHub

## What's Next?

Once you have Eva running:

1. **Build a frontend** - Use example clients as reference
2. **Add custom functions** - Extend Eva's capabilities
3. **Deploy to cloud** - Make it accessible anywhere
4. **Scale up** - Increase `MAX_USERS` as needed
5. **Add features** - Voice, NLP, integrations, etc.

---

**Welcome to Eva!** 🤖 You're now ready to build an amazing personal assistant.

Need help? Check the docs or open an issue!
