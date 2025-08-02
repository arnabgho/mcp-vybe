"""OAuth 2.0 authentication configuration and handlers for MCP server."""

import os
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load configuration
config = Config('.env')

# OAuth client setup
oauth = OAuth(config)

# Check if OAuth is enabled
ENABLE_OAUTH = os.getenv("ENABLE_OAUTH", "false").lower() == "true"
ENABLE_API_KEY_AUTH = os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
MCP_API_KEY = os.getenv("MCP_API_KEY")
OAUTH_REDIRECT_BASE_URL = os.getenv("OAUTH_REDIRECT_BASE_URL", "http://localhost:8000")

# Security bearer for token authentication
security = HTTPBearer(auto_error=False)

# Register OAuth providers if enabled
if ENABLE_OAUTH:
    # Google OAuth
    if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("Google OAuth provider registered")

    # GitHub OAuth
    if os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET"):
        oauth.register(
            name='github',
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'},
        )
        logger.info("GitHub OAuth provider registered")


async def get_user_info(provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from OAuth token based on provider."""
    client = oauth.create_client(provider)
    
    if provider == 'google':
        # Google includes userinfo in the token
        user_info = token.get('userinfo', {})
    elif provider == 'github':
        # GitHub requires an API call to get user info
        resp = await client.get('user', token=token)
        user_info = resp.json()
        
        # Get email separately if not included
        if not user_info.get('email'):
            email_resp = await client.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next((e['email'] for e in emails if e['primary']), None)
            if primary_email:
                user_info['email'] = primary_email
    else:
        user_info = {}
    
    return {
        'provider': provider,
        'id': user_info.get('id') or user_info.get('sub'),
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture') or user_info.get('avatar_url'),
        'raw': user_info
    }


async def verify_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Verify authentication using either OAuth token or API key.
    
    Returns user info dict if authenticated, raises HTTPException otherwise.
    """
    # Skip auth for health and root endpoints
    if request.url.path in ["/health", "/", "/auth/login", "/auth/callback"]:
        return None
    
    # If neither auth method is enabled, allow access
    if not ENABLE_OAUTH and not ENABLE_API_KEY_AUTH:
        return None
    
    # Try OAuth token first
    if ENABLE_OAUTH and credentials and credentials.credentials:
        try:
            from jwt_utils import verify_token
            token_data = verify_token(credentials.credentials)
            if token_data:
                return token_data
        except Exception as e:
            logger.debug(f"OAuth token verification failed: {e}")
    
    # Try API key authentication
    if ENABLE_API_KEY_AUTH and MCP_API_KEY:
        # Check Authorization header for API key
        if credentials and credentials.credentials == MCP_API_KEY:
            return {"type": "api_key", "authenticated": True}
        
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == MCP_API_KEY:
            return {"type": "api_key", "authenticated": True}
    
    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing authentication",
        headers={"WWW-Authenticate": "Bearer"}
    )


def create_oauth_routes(app):
    """Create OAuth routes for the application."""
    
    @app.get("/auth/login/{provider}")
    async def login(request: Request, provider: str):
        """Initiate OAuth login flow."""
        if not ENABLE_OAUTH:
            raise HTTPException(status_code=404, detail="OAuth is not enabled")
        
        client = oauth.create_client(provider)
        if not client:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not configured")
        
        redirect_uri = f"{OAUTH_REDIRECT_BASE_URL}/auth/callback/{provider}"
        return await client.authorize_redirect(request, redirect_uri)
    
    @app.get("/auth/callback/{provider}")
    async def callback(request: Request, provider: str):
        """Handle OAuth callback."""
        if not ENABLE_OAUTH:
            raise HTTPException(status_code=404, detail="OAuth is not enabled")
        
        client = oauth.create_client(provider)
        if not client:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not configured")
        
        try:
            token = await client.authorize_access_token(request)
            user_info = await get_user_info(provider, token)
            
            # Create JWT token
            from jwt_utils import create_access_token
            access_token = create_access_token(data={
                "sub": user_info.get('email'),
                "provider": provider,
                "user_id": user_info.get('id'),
                "name": user_info.get('name')
            })
            
            # Return token and user info
            return JSONResponse({
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_info
            })
            
        except OAuthError as e:
            logger.error(f"OAuth error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/auth/logout")
    async def logout(request: Request):
        """Handle logout (token revocation)."""
        # In a stateless JWT system, logout is handled client-side
        # Here we just acknowledge the logout request
        return JSONResponse({"message": "Logged out successfully"})
    
    @app.get("/auth/providers")
    async def list_providers():
        """List available OAuth providers."""
        providers = []
        if ENABLE_OAUTH:
            if os.getenv("GOOGLE_CLIENT_ID"):
                providers.append({
                    "name": "google",
                    "display_name": "Google",
                    "login_url": f"{OAUTH_REDIRECT_BASE_URL}/auth/login/google"
                })
            if os.getenv("GITHUB_CLIENT_ID"):
                providers.append({
                    "name": "github",
                    "display_name": "GitHub",
                    "login_url": f"{OAUTH_REDIRECT_BASE_URL}/auth/login/github"
                })
        
        return JSONResponse({
            "providers": providers,
            "oauth_enabled": ENABLE_OAUTH,
            "api_key_enabled": ENABLE_API_KEY_AUTH
        })