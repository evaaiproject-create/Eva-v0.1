# Eva Backend - Project Summary

## Overview

**Eva v0.1** is a complete, production-ready backend system for a personal assistant inspired by JARVIS (Marvel) and Baymax (Big Hero 6). It provides a scalable, cloud-based API with Google Cloud integration, multi-user support, cross-device synchronization, and an extensible function calling framework.

## Key Features

### 🔐 Authentication & Security
- **Google OAuth 2.0** integration for secure user authentication
- **JWT tokens** for stateless authentication
- **Bearer token** authentication for API endpoints
- **Environment-based** configuration for secrets
- **Input validation** using Pydantic models
- **Configurable user limits** (default: 5 users, easily scalable)

### 👥 User Management
- User profiles with customizable preferences
- Multi-device support per user
- Device registration and tracking
- Last login tracking
- Role-based user system (extensible)

### 🔄 Cross-Device Synchronization
- **Session-based sync** for seamless experiences
- Real-time state sharing across multiple devices
- Device-specific session data
- Session CRUD operations via REST API

### ⚡ Function Calling Framework
- **Dynamic function registry** - add capabilities without core changes
- **Built-in functions**:
  - `echo`: Echo back messages
  - `get_time`: Get current server time
  - `calculate`: Perform arithmetic operations
- **Function call history** for analytics
- **Easy extensibility** - add new functions in minutes
- **Async support** for I/O-bound operations

### 🗄️ Data Persistence
- **Google Cloud Firestore** for scalable NoSQL storage
- Collections for users, sessions, and function calls
- Automatic timestamps and metadata
- Optimized queries with proper indexing

### 📡 RESTful API
- **FastAPI framework** with automatic documentation
- **OpenAPI/Swagger** documentation at `/docs`
- **ReDoc** documentation at `/redoc`
- **CORS support** for cross-origin requests
- **Health check** endpoint for monitoring

## Project Structure

```
Eva-v0.1/
├── app/                        # Main application package
│   ├── api/                    # API endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── users.py           # User management endpoints
│   │   ├── sessions.py        # Session/sync endpoints
│   │   └── functions.py       # Function calling endpoints
│   ├── models/                # Data models
│   │   └── __init__.py        # Pydantic models for all entities
│   ├── services/              # Business logic
│   │   ├── auth_service.py    # Authentication service
│   │   ├── firestore_service.py # Database operations
│   │   └── function_service.py  # Function registry
│   ├── utils/                 # Utilities
│   │   └── dependencies.py    # FastAPI dependencies
│   └── config.py              # Configuration management
├── examples/                   # Client examples
│   ├── python_client.py       # Python client library
│   └── javascript_client.js   # JavaScript/Node.js client
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── verify_installation.py     # Installation verification script
├── Dockerfile                 # Docker container configuration
├── docker-compose.yml         # Docker Compose setup
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── Documentation/
    ├── README.md             # Main documentation
    ├── QUICKSTART.md         # Quick start guide
    ├── API_REFERENCE.md      # Complete API reference
    ├── GOOGLE_CLOUD_SETUP.md # Google Cloud setup guide
    ├── DEPLOYMENT.md         # Deployment instructions
    ├── EXTENDING.md          # Developer extension guide
    └── CHANGELOG.md          # Version history
```

## Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI 0.104.1
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic 2.5.0
- **Authentication**: Google OAuth 2.0, JWT (python-jose)
- **Database**: Google Cloud Firestore
- **Cloud Platform**: Google Cloud Platform
- **Containerization**: Docker

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login existing user
- `GET /auth/verify` - Verify JWT token

### Users
- `GET /users/me` - Get user profile
- `GET /users/me/devices` - List registered devices
- `POST /users/me/devices/{device_id}` - Register device
- `GET /users/me/preferences` - Get preferences
- `PUT /users/me/preferences` - Update preferences

### Sessions (Cross-Device Sync)
- `POST /sessions` - Create session
- `GET /sessions` - List user sessions
- `GET /sessions/{session_id}` - Get session
- `PUT /sessions/{session_id}` - Update session
- `DELETE /sessions/{session_id}` - Delete session

### Functions
- `GET /functions` - List available functions
- `POST /functions/call` - Execute function
- `GET /functions/history` - Get call history

### System
- `GET /` - API information
- `GET /health` - Health check

## Getting Started

### Quick Start (5 minutes)

```bash
# 1. Clone and install
git clone https://github.com/evaaiproject-create/Eva-v0.1.git
cd Eva-v0.1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Verify installation
python verify_installation.py

# 3. Configure (see GOOGLE_CLOUD_SETUP.md)
cp .env.example .env
# Edit .env with your Google Cloud credentials

# 4. Run
python main.py
```

Access at: http://localhost:8000/docs

### Prerequisites

1. Python 3.8+
2. Google Cloud account (free tier available)
3. Google Cloud project with Firestore enabled
4. OAuth 2.0 credentials
5. Service account key

## Documentation

### For Users
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in minutes
- **[README.md](README.md)** - Complete documentation
- **[GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)** - Google Cloud setup

### For Developers
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation
- **[EXTENDING.md](EXTENDING.md)** - How to add new functions
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guides

### Other
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[examples/](examples/)** - Client code examples

## Security Features

- ✅ OAuth 2.0 authentication
- ✅ JWT token-based authorization
- ✅ Environment variable secrets management
- ✅ Service account key protection
- ✅ Input validation
- ✅ CORS configuration
- ✅ Firestore security rules support
- ✅ Token expiration

## Deployment Options

Eva can be deployed to:
- **Google Cloud Run** (recommended)
- **Heroku**
- **AWS Elastic Beanstalk**
- **Docker/Docker Compose**
- **Any Python-compatible hosting**

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Extensibility

### Adding New Functions

```python
# Define function
def my_function(param: str) -> dict:
    return {"result": f"Processed {param}"}

# Register function
from app.services.function_service import function_registry

function_registry.register(
    name="my_function",
    func=my_function,
    description="My custom function",
    parameters_schema={
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    }
)
```

See [EXTENDING.md](EXTENDING.md) for complete guide.

## Scaling

### Current Capacity
- **Default**: 5 users (configurable via `MAX_USERS`)
- **Firestore Free Tier**: 50K reads, 20K writes per day
- **Suitable for**: Personal use, small teams, prototypes

### To Scale
1. Increase `MAX_USERS` environment variable
2. Enable Firestore billing (pay-as-you-go)
3. Add caching layer (Redis)
4. Implement rate limiting
5. Use load balancing

## Future Roadmap

### Planned Features
- Rate limiting per user
- Email/SMS notifications
- Advanced AI integration (OpenAI GPT)
- Voice assistant capabilities
- Real-time WebSocket connections
- Admin dashboard
- User analytics
- Webhook support
- More built-in functions

### Integrations
- Calendar (Google Calendar)
- Email (Gmail)
- Weather services
- News APIs
- Smart home devices
- Social media

## Development

### Run Tests
```bash
python verify_installation.py
```

### Start Development Server
```bash
uvicorn main:app --reload
```

### View Logs
Logs are output to stdout with INFO, WARNING, and ERROR levels.

### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

Eva is designed to be extended. To contribute:
1. Follow the patterns in existing code
2. Add tests for new features
3. Update documentation
4. Submit pull requests

## License

For educational and personal use.

## Support

- **Documentation**: Read the guides in this repository
- **Issues**: Open a GitHub issue
- **Examples**: Check the `examples/` directory

## Acknowledgments

Inspired by:
- **JARVIS** - Marvel Cinematic Universe
- **Baymax** - Big Hero 6

Built with:
- FastAPI
- Google Cloud Platform
- Modern Python best practices

## Quick Links

- [Quick Start Guide](QUICKSTART.md)
- [API Documentation](API_REFERENCE.md)
- [Extension Guide](EXTENDING.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Google Cloud Setup](GOOGLE_CLOUD_SETUP.md)

---

**Eva v0.1** - A personal assistant backend ready for your next project! 🤖

Questions? Check the documentation or open an issue on GitHub.
