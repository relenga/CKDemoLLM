"""
Test script for the FastAPI selllist endpoints
"""
import requests
import json

# Server URL
BASE_URL = "http://localhost:8002"

def test_selllist_endpoints():
    """Test all selllist endpoints"""
    
    print("🧪 Testing FastAPI Selllist Endpoints")
    print("="*50)
    
    # Test 1: Upload CSV file
    print("\n1. Testing CSV Upload...")
    try:
        with open('test_selllist.csv', 'rb') as f:
            files = {'file': ('test_selllist.csv', f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/api/selllist/upload", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Original records: {result['original_records']}")
            print(f"   Filtered records: {result['filtered_records']}")
            print(f"   Records removed: {result['records_removed']}")
            print(f"   Processing time: {result['processing_time']}s")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    # Test 2: Get stats
    print("\n2. Testing Stats Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/selllist/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats retrieved!")
            print(f"   Status: {stats['status']}")
            print(f"   Records: {stats['records']}")
            print(f"   Memory: {stats['memory_mb']} MB")
        else:
            print(f"❌ Stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    # Test 3: Get sample
    print("\n3. Testing Sample Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/selllist/sample?records=3")
        if response.status_code == 200:
            sample = response.json()
            print(f"✅ Sample retrieved!")
            print(f"   Status: {sample['status']}")
            print(f"   Total records: {sample['total_records']}")
            print(f"   Sample size: {sample['sample_size']}")
            if sample['status'] == 'loaded' and sample['sample_data']:
                print("   Sample cards:")
                for i, card in enumerate(sample['sample_data'][:2]):
                    print(f"     {i+1}. {card['SellProductName']} - ${card['SellTCGMarketPrice']}")
        else:
            print(f"❌ Sample failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Sample error: {e}")
    
    # Test 4: Clear data
    print("\n4. Testing Clear Endpoint...")
    try:
        response = requests.delete(f"{BASE_URL}/api/selllist/clear")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Clear successful!")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Clear failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Clear error: {e}")
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    test_selllist_endpoints()