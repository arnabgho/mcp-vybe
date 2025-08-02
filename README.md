# Vybe Virtual Try-On MCP Server

A FastMCP server that wraps the Replicate API for virtual try-on functionality, ready for deployment to Render.

## Setup

### Using UV (recommended)

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Replicate API token.

### Using pip (alternative)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Replicate API token.

## Local Testing

Run the server locally:
```bash
# With uv (recommended)
uv run python server.py

# Or with regular python
python server.py
```

The server will start on the default FastMCP port and expose the `virtual_tryon` tool.

## MCP Client Configuration

Add to your Claude Desktop or other MCP client configuration:

```json
{
  "mcpServers": {
    "vybe-virtual-tryon": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## Usage

The server exposes three tools:

### `test_connection`
Tests the connection and shows timeout configuration.

### `base64_to_url`
Converts base64 encoded images to data URIs for use with virtual_tryon:
- `base64_image`: Base64 encoded image string (with or without data:image prefix)
- `image_type`: Image type (png, jpg, jpeg, gif, webp) - default: png

Returns a data URI that can be used as `model_image` or `garment_image` in virtual_tryon.

### `virtual_tryon`
Performs virtual try-on with these parameters:
- `model_image`: URL or data URI of the person/model image
- `garment_image`: URL or data URI of the clothing item to try on
- Various optional parameters for customization

## Authentication

The server supports two authentication methods that can be used independently or together:

### OAuth 2.0 Authentication

Enable OAuth by setting `ENABLE_OAUTH=true` in your `.env` file. The server supports:
- **Google OAuth**: For Google account authentication
- **GitHub OAuth**: For GitHub account authentication

#### Setting up OAuth Providers

1. **Google OAuth**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `http://localhost:8000/auth/callback/google`
   - Copy Client ID and Client Secret to `.env`

2. **GitHub OAuth**:
   - Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Create a new OAuth App
   - Set Authorization callback URL: `http://localhost:8000/auth/callback/github`
   - Copy Client ID and Client Secret to `.env`

#### OAuth Endpoints

- `/auth/providers` - List available OAuth providers
- `/auth/login/{provider}` - Initiate OAuth login flow
- `/auth/callback/{provider}` - OAuth callback (handled automatically)
- `/auth/logout` - Logout endpoint

#### Using OAuth with MCP

After OAuth login, you'll receive a JWT token. Use it in requests:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" https://your-server/
```

### API Key Authentication

Enable API key authentication by setting `ENABLE_API_KEY_AUTH=true` in your `.env` file.

Generate a secure API key:
```bash
openssl rand -hex 32
```

Use the API key in requests:
```bash
# Using Authorization header
curl -H "Authorization: Bearer YOUR_API_KEY" https://your-server/

# Using X-API-Key header
curl -H "X-API-Key: YOUR_API_KEY" https://your-server/
```

### Combining Authentication Methods

You can enable both OAuth and API key authentication. This allows:
- Users to authenticate via OAuth for web interfaces
- Systems to use API keys for programmatic access

## Timeout Configuration

The server is configured with extended timeouts to handle long-running Replicate operations:
- MCP request timeout: 600 seconds (10 minutes)
- Replicate polling interval: 5 seconds
- Replicate timeout: 600 seconds (10 minutes)

If you still experience timeouts, you can adjust these in the server.py file.

## Deployment to Render

### Quick Deploy with render.yaml

1. Push your code to a GitHub repository
2. Connect the repository to Render
3. Render will automatically detect the `render.yaml` configuration
4. Add your `REPLICATE_API_TOKEN` in the Render dashboard under Environment Variables
5. Deploy!

The service includes health check endpoints:
- `/health` - Health check endpoint for Render monitoring
- `/` - Root endpoint with service status

### Manual Setup

If you prefer manual configuration:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - **Build Command**: `curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.cargo/env && uv sync --frozen --no-dev`
   - **Start Command**: `uv run python server.py`
   - **Health Check Path**: `/health`
4. Add environment variables:
   - `REPLICATE_API_TOKEN`: Your Replicate API token (required)
   - `PORT`: (leave empty, Render will auto-assign)
   - `HOST`: (leave empty, defaults to 0.0.0.0)
   
   For OAuth authentication (optional):
   - `ENABLE_OAUTH`: Set to `true` to enable OAuth
   - `JWT_SECRET_KEY`: Secret key for JWT tokens (generate with `openssl rand -hex 32`)
   - `OAUTH_REDIRECT_BASE_URL`: Your deployment URL (e.g., `https://your-service.onrender.com`)
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: For Google OAuth
   - `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`: For GitHub OAuth
   
   For API key authentication (optional):
   - `ENABLE_API_KEY_AUTH`: Set to `true` to enable API key auth
   - `MCP_API_KEY`: Your secure API key

### Using the Remote MCP Server

Once deployed, you can access the server at:
- **Health Check**: `https://your-service-name.onrender.com/health`
- **Root**: `https://your-service-name.onrender.com/`
- **MCP Protocol**: Use the base URL for MCP client connections

For MCP clients that support HTTP transport:

```json
{
  "mcpServers": {
    "vybe-virtual-tryon-remote": {
      "url": "https://your-service-name.onrender.com",
      "transport": "http"
    }
  }
}
```

Replace `your-service-name` with your actual Render service URL.

## Testing the Deployment

Use the included test script to verify your deployment is working:

```bash
# With uv (if using uv environment)
uv run python test_deployment.py https://your-service-name.onrender.com

# Or with regular python
python test_deployment.py https://your-service-name.onrender.com
```

This will test:
- Health check endpoint (`/health`)
- Root endpoint (`/`)
- Basic MCP server connectivity

Example output:
```
Testing deployment at: https://your-service.onrender.com
--------------------------------------------------

🧪 Testing Health Endpoint...
✅ Health check passed: {'status': 'healthy', 'service': 'vybe-virtual-tryon'}

🧪 Testing Root Endpoint...
✅ Root endpoint passed: {'message': 'Vybe Virtual Try-On MCP Server', 'status': 'running'}

🧪 Testing MCP Connection...
✅ MCP server is responding

==================================================
TEST RESULTS:
==================================================
✅ PASS - Health Endpoint
✅ PASS - Root Endpoint
✅ PASS - MCP Connection

Tests passed: 3/3

🎉 All tests passed! Deployment is working correctly.
```

### Docker Deployment (Alternative)

A Dockerfile is also included if you prefer containerized deployment. Render will automatically detect and use it if present.