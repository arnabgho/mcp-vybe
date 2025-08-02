# MCP Server Authentication and Registry Publishing Plan

## Overview

This document outlines the implementation plan for adding OAuth 2.0 authentication to the Vybe Virtual Try-On MCP server and preparing it for publication to an MCP registry.

## Phase 1: Add OAuth 2.0 Authentication to MCP Server

### 1.1 OAuth 2.0 Implementation

**Supported Providers:**
- Google (primary)
- GitHub (developer-friendly)
- Support for additional providers via configuration

**Implementation Architecture:**
```python
# OAuth flow structure
1. User initiates login → /auth/login/{provider}
2. Redirect to OAuth provider
3. Provider redirects back → /auth/callback/{provider}
4. Exchange code for tokens
5. Create JWT session token
6. Return token to client
```

### 1.2 Dependencies and Setup

**Required packages:**
```toml
authlib = "^1.3.0"          # OAuth client library
python-jose = "^3.3.0"      # JWT token handling
itsdangerous = "^2.1.2"     # Session security
python-multipart = "^0.0.6"  # Form data handling
```

### 1.3 Token Management Strategy

**Token Types:**
- **Access Token**: Short-lived (1 hour), used for API requests
- **Refresh Token**: Long-lived (30 days), used to get new access tokens
- **ID Token**: Contains user profile information

**Storage:**
- JWT tokens (stateless, client-side storage)
- Optional Redis for session management (future enhancement)

### 1.4 OAuth Configuration

**New files to create:**
- `auth.py`: OAuth configuration and handlers
- `jwt_utils.py`: JWT token utilities
- `models.py`: User and token models

**Environment variables:**
```bash
# OAuth Provider Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1

# OAuth Settings
OAUTH_REDIRECT_BASE_URL=https://your-domain.com
ENABLE_OAUTH=true

# Optional: Keep API key auth as fallback
ENABLE_API_KEY_AUTH=true
MCP_API_KEY=your_api_key_here
```

## Phase 2: OAuth Implementation Details

### 2.1 OAuth Flow Implementation

**auth.py - OAuth Configuration:**
```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config('.env')
oauth = OAuth(config)

# Register OAuth providers
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='github',
    client_id=config('GITHUB_CLIENT_ID'),
    client_secret=config('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)
```

### 2.2 JWT Token Management

**jwt_utils.py - Token Utilities:**
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 2.3 Authentication Endpoints

**OAuth Routes:**
```python
@mcp.custom_route("/auth/login/{provider}", ["GET"])
async def login(request: Request, provider: str):
    redirect_uri = request.url_for('callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

@mcp.custom_route("/auth/callback/{provider}", ["GET"])
async def callback(request: Request, provider: str):
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    
    # Get user info
    user_info = token.get('userinfo')
    if not user_info and provider == 'github':
        resp = await client.get('user')
        user_info = resp.json()
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user_info.get('email'), "provider": provider}
    )
    
    return JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_info
    })

@mcp.custom_route("/auth/logout", ["POST"])
async def logout(request: Request):
    # Token revocation logic here
    return JSONResponse({"message": "Logged out successfully"})
```

## Phase 3: Prepare for MCP Registry Publishing

### 3.1 Updated MCP Manifest File (`mcp.json`)

```json
{
  "name": "vybe-virtual-tryon",
  "version": "0.1.0",
  "description": "MCP server for AI-powered virtual clothing try-on using Replicate with OAuth authentication",
  "author": "Your Name",
  "license": "MIT",
  "repository": "https://github.com/yourusername/mcp-vybe-python",
  "transport": ["http", "sse"],
  "authentication": {
    "type": "oauth2",
    "providers": ["google", "github"],
    "optional_api_key": true
  },
  "environment": {
    "required": [
      "REPLICATE_API_TOKEN",
      "JWT_SECRET_KEY"
    ],
    "optional": [
      "GOOGLE_CLIENT_ID",
      "GOOGLE_CLIENT_SECRET",
      "GITHUB_CLIENT_ID",
      "GITHUB_CLIENT_SECRET",
      "MCP_API_KEY",
      "PORT",
      "HOST",
      "REPLICATE_POLL_INTERVAL",
      "REPLICATE_TIMEOUT"
    ]
  },
  "tools": [
    {
      "name": "test_connection",
      "description": "Test Replicate API connection"
    },
    {
      "name": "base64_to_url",
      "description": "Convert base64 images to data URIs"
    },
    {
      "name": "virtual_tryon",
      "description": "Perform AI virtual clothing try-on"
    }
  ],
  "endpoints": {
    "health": "/health",
    "root": "/"
  },
  "deployment": {
    "platforms": ["render", "docker", "heroku"],
    "minPythonVersion": "3.11"
  }
}
```

### 2.2 Registry Metadata

**Documentation Requirements:**
- Comprehensive usage guide
- API reference for all tools
- Security best practices
- Deployment instructions
- Example integrations

### 2.3 Package for Distribution

**Checklist:**
- [ ] All dependencies in `pyproject.toml`
- [ ] Deployment templates for major platforms
- [ ] CI/CD workflow for automated publishing
- [ ] Version tagging and release notes

## Phase 4: Security Enhancements

### 3.1 Rate Limiting

**Implementation:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/hour")
async def virtual_tryon(...):
    # Tool implementation
```

### 3.2 Request Validation

**Security Measures:**
- Input parameter validation
- URL sanitization for image inputs
- Base64 data size limits
- Request payload size limits

### 3.3 Logging and Monitoring

**Features:**
- Authentication audit logs
- API key usage tracking
- Failed authentication attempts
- Performance metrics

## Implementation Timeline

### Week 1: OAuth Implementation
- [x] Create implementation plan (this document)
- [ ] Add OAuth dependencies
- [ ] Create auth.py and jwt_utils.py
- [ ] Implement OAuth endpoints
- [ ] Update server.py with OAuth middleware

### Week 2: Integration & Testing
- [ ] Test OAuth flow with Google
- [ ] Test OAuth flow with GitHub
- [ ] Implement token refresh logic
- [ ] Add user session management
- [ ] Create OAuth test script

### Week 3: Registry Preparation
- [ ] Update mcp.json manifest
- [ ] Update documentation
- [ ] Create deployment guides
- [ ] Test deployment scenarios

### Week 4: Security & Polish
- [ ] Add rate limiting per user
- [ ] Implement comprehensive logging
- [ ] Security audit
- [ ] Final testing and release

## Testing Strategy

### Authentication Tests
1. Valid API key authentication
2. Invalid API key rejection
3. Missing API key handling
4. Rate limit enforcement

### Integration Tests
1. End-to-end tool execution with auth
2. Deployment verification
3. Registry compliance checks

## Deployment Considerations

### Environment Variables
```bash
# Required
REPLICATE_API_TOKEN=your_replicate_token
JWT_SECRET_KEY=your_jwt_secret_key

# OAuth Providers (at least one required if ENABLE_OAUTH=true)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# OAuth Configuration
ENABLE_OAUTH=true
OAUTH_REDIRECT_BASE_URL=https://your-domain.com
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1

# Optional API Key Auth (fallback)
ENABLE_API_KEY_AUTH=true
MCP_API_KEY=your_secure_api_key

# Server Configuration
PORT=8000
HOST=0.0.0.0
RATE_LIMIT_PER_HOUR=100
```

### Security Best Practices
1. **OAuth Security**:
   - Use HTTPS in production (required for OAuth)
   - Implement PKCE for public clients
   - Validate redirect URIs
   - Use state parameter to prevent CSRF

2. **Token Security**:
   - Use strong JWT secret keys
   - Implement token rotation
   - Short-lived access tokens (1 hour)
   - Secure token storage on client side

3. **General Security**:
   - Monitor for suspicious activity
   - Rate limiting per user
   - Use environment variables for all secrets
   - Never commit secrets to version control
   - Regular security audits

## Future Enhancements

1. **OAuth Enhancements**:
   - Support for more providers (Microsoft, Auth0)
   - Social login UI
   - Account linking between providers
   - OAuth2 device flow for CLI clients

2. **Session Management**:
   - Redis-based session storage
   - Session revocation endpoints
   - Multi-device session tracking
   - Remember me functionality

3. **Advanced Security**:
   - Two-factor authentication
   - IP allowlisting
   - Anomaly detection
   - Security event webhooks

4. **User Management**:
   - User profile endpoints
   - Permission/role system
   - Usage quotas per user
   - Admin dashboard

## Commands to Remember

```bash
# Run lint and typecheck
uv run ruff check .
uv run mypy server.py

# Run tests
uv run pytest

# Build for deployment
uv sync --frozen --no-dev

# Test deployment locally
uv run python server.py
```

## Notes

- Always test authentication changes thoroughly before deployment
- Keep backward compatibility when possible
- Document all breaking changes
- Follow semantic versioning for releases