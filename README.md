# Vybe Virtual Try-On MCP Server

A FastMCP server that wraps the Replicate API for virtual try-on functionality, ready for deployment to Render.

## Setup

### Using UV (recommended)

1. Install dependencies:
```bash
uv pip install -e .
```

### Using pip

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
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Health Check Path**: `/health`
4. Add environment variables:
   - `REPLICATE_API_TOKEN`: Your Replicate API token (required)
   - `PORT`: (leave empty, Render will auto-assign)
   - `HOST`: (leave empty, defaults to 0.0.0.0)

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