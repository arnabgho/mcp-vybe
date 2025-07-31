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

### Manual Setup

If you prefer manual configuration:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - **Build Command**: `pip install -e .`
   - **Start Command**: `python server.py`
4. Add environment variables:
   - `REPLICATE_API_TOKEN`: Your Replicate API token (required)
   - `MCP_TRANSPORT`: `http` (required for remote access)
   - `PORT`: (leave empty, Render will auto-assign)

### Using the Remote MCP Server

Once deployed, configure your MCP client to connect to the remote server:

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

### Docker Deployment (Alternative)

A Dockerfile is also included if you prefer containerized deployment. Render will automatically detect and use it if present.