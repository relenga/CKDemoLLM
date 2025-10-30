import requests
import json

def test_post_endpoint():
    url = "http://localhost:8002/api/buylist/upload"
    
    try:
        print("Testing POST request to buylist upload endpoint...")
        response = requests.post(url, json={})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            print(f"Total Records: {data.get('total_records')}")
            print(f"Processing Time: {data.get('processing_time')}s")
            
            if 'sample_records' in data and data['sample_records']:
                print(f"\nSample Records (first 2):")
                for i, record in enumerate(data['sample_records'][:2]):
                    print(f"  Record {i+1}: {record}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the server is running on port 8002")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_post_endpoint()