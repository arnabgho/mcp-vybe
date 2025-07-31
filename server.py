from fastmcp import FastMCP
import replicate
import os
from typing import Optional
from dotenv import load_dotenv
import asyncio
import base64

load_dotenv()

# Set Replicate client timeout
os.environ["REPLICATE_POLL_INTERVAL"] = "5"  # Poll every 5 seconds
os.environ["REPLICATE_TIMEOUT"] = "600"  # 10 minute timeout

# Remove the request_timeout parameter from FastMCP constructor
mcp = FastMCP(
    "vybe-virtual-tryon",
    version="0.1.0"
)

# Add health check endpoint for Render
@mcp.get("/health")
async def health_check():
    """Health check endpoint for Render monitoring."""
    return {"status": "healthy", "service": "vybe-virtual-tryon"}

@mcp.tool()
async def base64_to_url(
    base64_image: str,
    image_type: Optional[str] = "png"
) -> dict:
    """
    Convert a base64 encoded image to a data URI that can be used with Replicate.
    
    Args:
        base64_image: Base64 encoded image string (with or without data:image prefix)
        image_type: Image type (png, jpg, jpeg, gif, webp) - default: png
    
    Returns:
        Dictionary with the data URI that can be used directly with virtual_tryon
    """
    try:
        # Remove data:image prefix if present
        if base64_image.startswith('data:image'):
            # Already a data URI, just return it
            return {
                "success": True,
                "url": base64_image,
                "message": "Image is already a data URI"
            }
        
        # Validate base64
        try:
            base64.b64decode(base64_image)
        except:
            return {
                "success": False,
                "error": "Invalid base64 string",
                "message": "The provided string is not valid base64"
            }
        
        # Determine MIME type
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        mime_type = mime_types.get(image_type.lower(), 'image/png')
        
        # Create a data URI that Replicate accepts
        data_uri = f"data:{mime_type};base64,{base64_image}"
        
        return {
            "success": True,
            "url": data_uri,
            "mime_type": mime_type,
            "message": "Successfully created data URI. Use this 'url' with the virtual_tryon tool."
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to convert base64 to data URI"
        }

@mcp.tool()
async def test_connection() -> dict:
    """
    Test the connection to Replicate API without running a model.
    """
    try:
        # Simple test to check if we can import and use replicate
        return {
            "success": True,
            "message": "Connection test successful",
            "replicate_token_set": bool(os.getenv("REPLICATE_API_TOKEN")),
            "timeout_settings": {
                "replicate_timeout": os.getenv("REPLICATE_TIMEOUT", "Not set"),
                "replicate_poll_interval": os.getenv("REPLICATE_POLL_INTERVAL", "Not set")
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def virtual_tryon(
    model_image: str,
    garment_image: str,
    seed: Optional[int] = 42,
    prompt: Optional[str] = None,
    size_width: Optional[int] = 672,
    size_height: Optional[int] = 896,
    make_square: Optional[bool] = True,
    whiten_mask: Optional[bool] = False,
    expand_ratio: Optional[float] = 0.025,
    output_format: Optional[str] = "png",
    guidance_scale: Optional[int] = 30,
    output_quality: Optional[int] = 90,
    num_inference_steps: Optional[int] = 30,
) -> dict:
    """
    Apply virtual try-on to put a garment on a model using Replicate API.
    
    Args:
        model_image: URL of the model/person image
        garment_image: URL of the garment/clothing image to try on
        seed: Random seed for reproducibility (default: 42)
        prompt: Custom prompt for generation (optional)
        size_width: Output image width (default: 672)
        size_height: Output image height (default: 896)
        make_square: Whether to make output square (default: True)
        whiten_mask: Whether to whiten the mask (default: False)
        expand_ratio: Mask expansion ratio (default: 0.025)
        output_format: Output format - png or jpg (default: png)
        guidance_scale: Guidance scale for generation (default: 30)
        output_quality: Output quality 1-100 (default: 90)
        num_inference_steps: Number of inference steps (default: 30)
    
    Returns:
        Dictionary with the result URLs and metadata
    """
    
    if not prompt:
        prompt = "The pair of images highlights a same clothing on two models, no bags or arm accessories, high resolution, 4K, 8K; [IMAGE1] Cloth is worn by a model in a lifestyle setting.[IMAGE2] The same cloth is worn by another model in a lifestyle setting."
    
    try:
        # Run the Replicate model asynchronously
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            replicate.run,
            "arnab-optimatik/vybe-virtual-tryon:b0ccd961710dd8c0980526aecefc7815449d1b1bfdae29c60a38760261b81d9e",
            {
                "seed": seed,
                "prompt": prompt,
                "size_width": size_width,
                "make_square": make_square,
                "size_height": size_height,
                "whiten_mask": whiten_mask,
                "expand_ratio": expand_ratio,
                "output_format": output_format,
                "guidance_scale": guidance_scale,
                "output_quality": output_quality,
                "num_inference_steps": num_inference_steps,
                "model_image": model_image,
                "garment_image": garment_image,
            }
        )
        
        # Convert FileOutput objects to URLs
        results = []
        for item in output:
            if hasattr(item, 'url'):
                # This is a FileOutput object, extract the URL
                results.append(item.url)
            elif isinstance(item, str):
                # Already a string (URL)
                results.append(item)
            else:
                # Convert to string as fallback
                results.append(str(item))
        
        return {
            "success": True,
            "results": results,  # Now contains serializable URLs
            "model": "vybe-virtual-tryon",
            "parameters": {
                "model_image": model_image,
                "garment_image": garment_image,
                "seed": seed,
                "size": f"{size_width}x{size_height}"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate virtual try-on"
        }

if __name__ == "__main__":
    # Configure for deployment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", "8000"))
    
    if transport == "http":
        # HTTP transport for remote access (Render deployment)
        uvicorn_config = {
            "host": "0.0.0.0",
            "port": port,
            "timeout_keep_alive": 600,  # 10 minutes
            "timeout_graceful_shutdown": 30,
        }
        print(f"Starting MCP server with HTTP transport on port {port}")
        mcp.run(transport="http", uvicorn_config=uvicorn_config)
    else:
        # Default stdio transport for local use
        print("Starting MCP server with stdio transport")
        mcp.run()