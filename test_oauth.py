#!/usr/bin/env python3
"""Test script for OAuth authentication flow."""

import asyncio
import httpx
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs
import json


async def test_oauth_flow(base_url: str = "http://localhost:8000"):
    """Test the OAuth authentication flow."""
    
    print(f"Testing OAuth flow at: {base_url}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Check available providers
        print("\n🧪 Testing OAuth Providers Endpoint...")
        try:
            response = await client.get(f"{base_url}/auth/providers")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OAuth providers endpoint working")
                print(f"   OAuth enabled: {data.get('oauth_enabled', False)}")
                print(f"   API key enabled: {data.get('api_key_enabled', False)}")
                print(f"   Available providers: {[p['name'] for p in data.get('providers', [])]}")
                
                if not data.get('oauth_enabled'):
                    print("\n⚠️  OAuth is not enabled. Set ENABLE_OAUTH=true in .env")
                    return
                
                if not data.get('providers'):
                    print("\n⚠️  No OAuth providers configured. Add provider credentials to .env")
                    return
                    
            else:
                print(f"❌ Failed to get providers: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            return
        
        # Test 2: Test unauthenticated access
        print("\n🧪 Testing Unauthenticated Access...")
        try:
            response = await client.get(f"{base_url}/test_connection")
            if response.status_code == 401:
                print("✅ Unauthenticated access correctly rejected")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: API Key authentication (if enabled)
        api_key = input("\n📝 Enter API key (or press Enter to skip): ").strip()
        if api_key:
            print("\n🧪 Testing API Key Authentication...")
            try:
                headers = {"X-API-Key": api_key}
                response = await client.post(
                    f"{base_url}/test_connection",
                    headers=headers,
                    json={}
                )
                if response.status_code == 200:
                    print("✅ API key authentication successful")
                else:
                    print(f"❌ API key authentication failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Test 4: OAuth login flow
        providers_response = await client.get(f"{base_url}/auth/providers")
        providers = providers_response.json().get('providers', [])
        
        if providers:
            print("\n🧪 Testing OAuth Login Flow...")
            print("Available providers:")
            for i, provider in enumerate(providers):
                print(f"  {i+1}. {provider['display_name']}")
            
            choice = input("\nSelect provider (number) or press Enter to skip: ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(providers):
                    provider = providers[idx]
                    login_url = provider['login_url']
                    
                    print(f"\n🌐 Opening browser for {provider['display_name']} login...")
                    print(f"Login URL: {login_url}")
                    
                    # Open browser for OAuth flow
                    webbrowser.open(login_url)
                    
                    print("\n⏳ Complete the OAuth flow in your browser...")
                    print("After authentication, you'll be redirected to a callback URL.")
                    print("The URL will contain your access token.")
                    
                    callback_url = input("\n📝 Paste the callback URL here: ").strip()
                    
                    if callback_url:
                        # Parse the callback URL to extract token or error
                        parsed = urlparse(callback_url)
                        if '/auth/callback/' in parsed.path:
                            print("\n✅ OAuth flow completed!")
                            print("Check the browser response for your access token")
                            
                            # Test authenticated request with token
                            token = input("\n📝 Enter the access token from the response: ").strip()
                            if token:
                                print("\n🧪 Testing Authenticated Request...")
                                headers = {"Authorization": f"Bearer {token}"}
                                response = await client.post(
                                    f"{base_url}/test_connection",
                                    headers=headers,
                                    json={}
                                )
                                if response.status_code == 200:
                                    print("✅ Authenticated request successful!")
                                    result = response.json()
                                    print(f"Response: {json.dumps(result, indent=2)}")
                                else:
                                    print(f"❌ Authenticated request failed: {response.status_code}")


def main():
    """Main entry point."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("=" * 50)
    print("OAuth Authentication Test Script")
    print("=" * 50)
    print(f"Server URL: {base_url}")
    print("\nMake sure the server is running with OAuth enabled:")
    print("  ENABLE_OAUTH=true")
    print("  At least one provider configured (Google/GitHub)")
    print("=" * 50)
    
    asyncio.run(test_oauth_flow(base_url))
    
    print("\n" + "=" * 50)
    print("✅ OAuth testing completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()