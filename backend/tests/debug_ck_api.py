"""
Debug script to check what we're getting from Card Kingdom API
"""

import asyncio
import aiohttp

async def debug_ck_api():
    """Debug the Card Kingdom API response."""
    print("🔍 Debugging Card Kingdom API Response")
    print("=" * 50)
    
    url = "https://www.cardkingdom.com/json/buylist.jsonp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Fetching from: {url}")
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
                
                raw_data = await response.text()
                print(f"Data length: {len(raw_data):,} characters")
                print(f"First 200 characters: {raw_data[:200]}")
                print(f"Last 200 characters: {raw_data[-200:]}")
                
                # Check for JSONP wrapper
                if raw_data.startswith('ckCardList('):
                    print("✅ JSONP wrapper 'ckCardList(' found at start")
                else:
                    print("❌ No JSONP wrapper found at start")
                
                if raw_data.endswith(');'):
                    print("✅ JSONP wrapper ending ');' found")
                else:
                    print("❌ No JSONP wrapper ending found")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ck_api())