from fastmcp import FastMCP
import replicate
import os
from typing import Optional
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Set Replicate client timeout
os.environ["REPLICATE_POLL_INTERVAL"] = "5"  # Poll every 5 seconds
os.environ["REPLICATE_TIMEOUT"] = "600"  # 10 minute timeout

# Remove the request_timeout parameter from FastMCP constructor
mcp = FastMCP(
    "vybe-virtual-tryon",
    version="0.1.0"
)

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
    # If you need to configure HTTP timeout when running the server, 
    # you can pass uvicorn_config to the run method
    uvicorn_config = {
        "timeout_keep_alive": 600,  # 10 minutes
        "timeout_graceful_shutdown": 30,
    }
    
    # For stdio transport (default), timeout is handled by the client
    mcp.run()
    
    # If you need to run with HTTP transport and specific timeout config:
    # mcp.run(transport="http", uvicorn_config=uvicorn_config)