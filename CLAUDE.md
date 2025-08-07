# Vybe Virtual Try-On MCP Server

AI-powered virtual clothing try-on using Replicate with optional WorkOS AuthKit authentication.

## Quick Start

```bash
# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your REPLICATE_API_TOKEN and TAVILY_API_KEY (optional)

# Run server
uv run python server.py
```

## Authentication (Optional)

Enable WorkOS AuthKit by setting:
```bash
AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
BASE_URL=https://your-deployment-url.com
```

Prerequisites:
1. Create WorkOS account at https://workos.com
2. Create AuthKit instance
3. Enable Dynamic Client Registration
4. Set environment variables above

When enabled, all API calls require authentication through AuthKit.

## Available Tools

- **virtual_tryon**: AI-powered clothing try-on
  - `model_image`: Person image (URL or base64)
  - `garment_image`: Clothing image (URL or base64)
  - Additional parameters: seed, prompt, size_width, size_height, etc.

- **style_recommendation_today**: Get clothing recommendations and try them on
  - `user_image`: Your photo (URL or base64)
  - `search_keyword`: Style search term (e.g., "summer dress", "business casual")
  - `max_results`: Number of items to try (default: 3)
  - Requires `TAVILY_API_KEY` in environment

- **base64_to_url**: Convert base64 to data URI
- **test_connection**: Test Replicate connection

## Deployment

### Render
1. Connect GitHub repository
2. Add environment variables:
   - `REPLICATE_API_TOKEN` (required)
   - `TAVILY_API_KEY` (required for style_recommendation_today)
   - `AUTHKIT_DOMAIN` (optional)
   - `BASE_URL` (if using AuthKit)
3. Deploy

### Requirements
- Python >= 3.11
- FastMCP >= 2.11.0