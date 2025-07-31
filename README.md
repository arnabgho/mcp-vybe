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

The server exposes two tools:

### `test_connection`
Tests the connection and shows timeout configuration.

### `virtual_tryon`
Performs virtual try-on with these parameters:
- `model_image`: URL of the person/model image
- `garment_image`: URL of the clothing item to try on
- Various optional parameters for customization

## Timeout Configuration

The server is configured with extended timeouts to handle long-running Replicate operations:
- MCP request timeout: 600 seconds (10 minutes)
- Replicate polling interval: 5 seconds
- Replicate timeout: 600 seconds (10 minutes)

If you still experience timeouts, you can adjust these in the server.py file.

## Deployment to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables:
   - `REPLICATE_API_TOKEN`: Your Replicate API token
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python server.py`

For remote MCP usage, configure your client to connect to the Render service URL.