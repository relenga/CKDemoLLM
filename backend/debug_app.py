#!/usr/bin/env python3
"""
Debug script to test FastAPI app routing
"""

def test_imports():
    print("=== Testing imports ===")
    
    try:
        from app.api.endpoints import router as endpoints_router
        print(f"✓ endpoints_router imported successfully")
        print(f"  - Routes in endpoints_router: {len(endpoints_router.routes)}")
        for i, route in enumerate(endpoints_router.routes):
            path = getattr(route, 'path', 'no path')
            methods = getattr(route, 'methods', ['no methods'])
            print(f"    {i+1}: {path} {methods}")
    except Exception as e:
        print(f"✗ Error importing endpoints_router: {e}")
        return False
    
    try:
        from app.api.routes import api_router
        print(f"✓ api_router imported successfully")
        print(f"  - Routes in api_router: {len(api_router.routes)}")
    except Exception as e:
        print(f"✗ Error importing api_router: {e}")
        return False
    
    try:
        from main import app
        print(f"✓ main app imported successfully")
        print(f"  - Routes in main app: {len(app.routes)}")
        for i, route in enumerate(app.routes):
            path = getattr(route, 'path', 'no path')
            methods = getattr(route, 'methods', ['no methods'])
            print(f"    {i+1}: {path} {methods}")
    except Exception as e:
        print(f"✗ Error importing main app: {e}")
        return False
    
    return True

def test_specific_endpoints():
    print("\n=== Testing specific endpoint availability ===")
    try:
        from main import app
        # Look for our specific endpoints
        buylist_routes = []
        for route in app.routes:
            path = getattr(route, 'path', '')
            if 'buylist' in path:
                buylist_routes.append(route)
        
        print(f"Found {len(buylist_routes)} buylist-related routes:")
        for route in buylist_routes:
            path = getattr(route, 'path', 'no path')
            methods = getattr(route, 'methods', ['no methods'])
            print(f"  - {path} {methods}")
            
        if len(buylist_routes) == 0:
            print("❌ No buylist routes found!")
        else:
            print("✓ Buylist routes are registered")
            
    except Exception as e:
        print(f"✗ Error testing endpoints: {e}")

if __name__ == "__main__":
    print("FastAPI App Debug Test")
    print("=" * 40)
    
    success = test_imports()
    if success:
        test_specific_endpoints()
    else:
        print("Import test failed, skipping endpoint test")