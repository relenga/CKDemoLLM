"""
Minimal test to identify the 500 error in the upload endpoint.
"""
import asyncio
import aiohttp
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buylist_core import process_buylist_data

async def test_upload_components():
    """Test each component of the upload process separately."""
    print("🔍 Testing Upload Components")
    print("=" * 50)
    
    # Test 1: Test aiohttp import and basic functionality
    print("\n1. Testing aiohttp...")
    try:
        print("   ✅ aiohttp imported successfully")
        
        # Test 2: Test basic HTTP request
        print("\n2. Testing HTTP request...")
        url = "https://www.cardkingdom.com/json/buylist.jsonp"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"   ❌ HTTP Error: {response.status}")
                    return False
                
                raw_data = await response.text()
                print(f"   ✅ HTTP request successful: {len(raw_data):,} characters")
        
        # Test 3: Test data processing
        print("\n3. Testing data processing...")
        transformed_records, total_count = process_buylist_data(raw_data, save_to_dataframe=True)
        print(f"   ✅ Data processing successful: {total_count:,} records")
        
        # Test 4: Test stats
        print("\n4. Testing stats...")
        from buylist_core import get_buylist_stats
        stats = get_buylist_stats()
        print(f"   ✅ Stats successful: {stats['records']:,} records loaded")
        
        print("\n🎉 All components work individually!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_upload_components())
    if success:
        print("\n✅ All upload components are working!")
        print("The 500 error must be in the FastAPI endpoint setup.")
    else:
        print("\n❌ Found the issue in the upload components.")