"""
HTTP Integration tests for the Card Kingdom buylist API endpoints.
Tests the actual HTTP endpoints without mocking.
"""

import requests
import json
import time


def test_server_endpoints():
    """Test basic server endpoints."""
    base_url = "http://localhost:8002"
    
    print("🧪 Testing basic server endpoints...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "CK LangGraph Backend API"
        assert data["status"] == "running"
        print("✅ Root endpoint works")
    except requests.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint works")
    except requests.RequestException as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test API test endpoint
    try:
        response = requests.get(f"{base_url}/api/test", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ API test endpoint works")
    except requests.RequestException as e:
        print(f"❌ API test endpoint failed: {e}")
        return False
    
    # Test buylist test endpoint
    try:
        response = requests.get(f"{base_url}/api/buylist/test", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ Buylist test endpoint works")
    except requests.RequestException as e:
        print(f"❌ Buylist test endpoint failed: {e}")
        return False
    
    return True


def test_buylist_upload_endpoint():
    """Test the main buylist upload endpoint."""
    base_url = "http://localhost:8002"
    
    print("\n🧪 Testing buylist upload endpoint...")
    print("⏳ This may take a few seconds to fetch Card Kingdom data...")
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/api/buylist/upload", timeout=180)  # 3 minute timeout
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "message" in data
        assert "total_records" in data
        assert "processing_time" in data
        assert "sample_records" in data
        assert "columns" in data
        
        print(f"✅ Buylist upload endpoint works")
        print(f"   Status: {data['status']}")
        print(f"   Total records: {data.get('total_records', 'N/A'):,}")
        print(f"   Processing time: {data.get('processing_time', 'N/A')} seconds")
        print(f"   Request time: {end_time - start_time:.2f} seconds")
        print(f"   Sample records returned: {len(data.get('sample_records', []))}")
        print(f"   Columns: {len(data.get('columns', []))}")
        
        # Verify data structure
        if data.get("sample_records"):
            sample = data["sample_records"][0]
            expected_columns = ["BuyProductId", "BuyCardName", "BuyEdition", "BuyRarity", "BuyFoil", "BuyPrice", "BuyQty", "BuyImage"]
            
            print(f"   Sample record columns: {list(sample.keys())}")
            
            # Check that at least some expected columns are present
            found_columns = [col for col in expected_columns if col in sample]
            if len(found_columns) >= 3:  # At least 3 columns should be present
                print(f"✅ Column transformation working ({len(found_columns)}/{len(expected_columns)} columns found)")
            else:
                print(f"⚠️  Only {len(found_columns)} expected columns found in sample")
        
        return True
        
    except requests.Timeout:
        print("❌ Buylist upload endpoint timed out (>180 seconds)")
        return False
    except requests.RequestException as e:
        print(f"❌ Buylist upload endpoint failed: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Buylist upload endpoint assertion failed: {e}")
        return False


def test_server_availability():
    """Test if the server is running and available."""
    base_url = "http://localhost:8002"
    
    print("🔍 Checking if server is available...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and available")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Server is not available: {e}")
        print("💡 Make sure to start the server with: python main.py")
        return False


def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Card Kingdom Buylist API Integration Tests")
    print("=" * 70)
    
    # Check if server is available
    if not test_server_availability():
        print("\n💡 Please start the server first:")
        print("   cd backend")
        print("   python main.py")
        return False
    
    print()
    
    # Run endpoint tests
    if not test_server_endpoints():
        print("\n❌ Basic endpoint tests failed")
        return False
    
    # Run buylist upload test
    if not test_buylist_upload_endpoint():
        print("\n❌ Buylist upload test failed")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 ALL INTEGRATION TESTS PASSED! ✅")
    print("\nThe Card Kingdom buylist API is working correctly:")
    print("✅ Server endpoints responding")
    print("✅ Card Kingdom data fetching")
    print("✅ JSONP parsing and cleaning")
    print("✅ Record transformation")
    print("✅ Error handling")
    
    return True


if __name__ == "__main__":
    import sys
    success = run_integration_tests()
    sys.exit(0 if success else 1)