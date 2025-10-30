"""
Simple test script to verify FastAPI server and dataframe endpoints work correctly.
"""

import requests
import time
import json

def test_server_endpoints():
    """Test the FastAPI server endpoints."""
    print("🧪 Testing FastAPI Server Endpoints")
    print("=" * 60)
    
    # Try different ports in case server is running on a different port
    ports_to_try = [8002, 8003, 8004]
    base_url = None
    
    for port in ports_to_try:
        try:
            test_url = f"http://127.0.0.1:{port}"
            response = requests.get(f"{test_url}/api/health", timeout=2)
            if response.status_code == 200:
                base_url = test_url
                print(f"   ✅ Found server running on port {port}")
                break
        except:
            continue
    
    if not base_url:
        print("   ❌ No server found on any port. Please start the server first:")
        print("   💡 Run: python main.py")
        return False
    
    # Test 1: Health check
    print("\n💓 Test 1: Health check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Health check passed: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print("   💡 Make sure the server is running: python main.py")
        return False
    
    # Test 2: Check initial dataframe stats
    print("\n📊 Test 2: Initial dataframe stats")
    try:
        response = requests.get(f"{base_url}/api/buylist/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Status: {stats['status']}")
            print(f"   Records: {stats['records']:,}")
            print(f"   Memory: {stats['memory_mb']} MB")
        else:
            print(f"   ❌ Stats endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Stats request failed: {e}")
        return False
    
    # Test 3: Upload buylist data
    print("\n📡 Test 3: Upload buylist data")
    try:
        upload_start = time.time()
        response = requests.post(f"{base_url}/api/buylist/upload", timeout=30)
        upload_time = time.time() - upload_start
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   Status: {result['status']}")
            print(f"   Records: {result['total_records']:,}")
            print(f"   Processing time: {result['processing_time']}s")
            print(f"   Total time: {upload_time:.2f}s")
            
            # Check dataframe stats
            if 'dataframe_stats' in result:
                df_stats = result['dataframe_stats']
                print(f"   Dataframe status: {df_stats['status']}")
                print(f"   Dataframe records: {df_stats['records']:,}")
                print(f"   Dataframe memory: {df_stats['memory_mb']} MB")
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Upload request failed: {e}")
        return False
    
    # Test 4: Verify dataframe stats after upload
    print("\n💾 Test 4: Dataframe stats after upload")
    try:
        response = requests.get(f"{base_url}/api/buylist/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Status: {stats['status']}")
            print(f"   Records: {stats['records']:,}")
            print(f"   Memory: {stats['memory_mb']} MB")
            
            if stats['records'] > 140000:
                print("   ✅ Dataframe contains expected number of records")
            else:
                print(f"   ❌ Expected 140K+ records, got {stats['records']:,}")
                return False
        else:
            print(f"   ❌ Stats endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Stats request failed: {e}")
        return False
    
    # Test 5: Clear dataframe
    print("\n🗑️ Test 5: Clear dataframe")
    try:
        response = requests.delete(f"{base_url}/api/buylist/clear", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Clear successful: {result['message']}")
        else:
            print(f"   ❌ Clear failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Clear request failed: {e}")
        return False
    
    # Test 6: Verify dataframe is cleared
    print("\n✅ Test 6: Verify dataframe is cleared")
    try:
        response = requests.get(f"{base_url}/api/buylist/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Status: {stats['status']}")
            print(f"   Records: {stats['records']:,}")
            
            if stats['status'] == 'empty' and stats['records'] == 0:
                print("   ✅ Dataframe properly cleared")
            else:
                print(f"   ❌ Expected empty dataframe, got status: {stats['status']}, records: {stats['records']}")
                return False
        else:
            print(f"   ❌ Stats endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Stats request failed: {e}")
        return False
    
    print("\n🎉 ALL SERVER TESTS PASSED! ✅")
    print("✅ Health check works")
    print("✅ Buylist upload works and saves to dataframe")
    print("✅ Dataframe stats endpoint works")
    print("✅ Dataframe clear endpoint works")
    print("✅ Data persistence confirmed")
    return True

if __name__ == "__main__":
    success = test_server_endpoints()
    if success:
        print("\n🎯 CONCLUSION: Your FastAPI server with dataframe storage is READY!")
        print("✅ All endpoints work correctly")
        print("✅ Data is properly stored and managed")
        print("✅ Your frontend can safely use these endpoints")
    else:
        print("\n❌ CONCLUSION: There are issues with the server endpoints")
        print("💡 Make sure the server is running with: python main.py")
    
    print("\n" + "=" * 60)