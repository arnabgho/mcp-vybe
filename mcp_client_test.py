from fastmcp import Client
import asyncio

async def main():
    async with Client("http://0.0.0.0:8000/mcp/", auth="oauth") as client:
        assert await client.ping()

if __name__ == "__main__":
    asyncio.run(main())