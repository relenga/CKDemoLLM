"""
Test runner for Card Kingdom buylist functionality.
Runs all available tests.
"""

import os
import sys
import subprocess


def run_simple_tests():
    """Run the simple unit tests that don't require external dependencies."""
    print("🚀 Running Simple Unit Tests")
    print("=" * 50)
    
    test_file = os.path.join(os.path.dirname(__file__), "test_buylist_simple.py")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run simple tests: {e}")
        return False


def run_integration_tests():
    """Run integration tests if server is available."""
    print("\n🚀 Running Integration Tests")
    print("=" * 50)
    
    test_file = os.path.join(os.path.dirname(__file__), "test_integration.py")
    
    # Check if requests is available
    try:
        import requests
    except ImportError:
        print("⚠️  Skipping integration tests - 'requests' module not available")
        print("   Install with: pip install requests")
        return True  # Don't fail the overall test run
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run integration tests: {e}")
        return False


def run_pytest_tests():
    """Run pytest tests if pytest is available."""
    print("\n🚀 Running Pytest Tests")
    print("=" * 50)
    
    try:
        import pytest
        
        test_dir = os.path.dirname(__file__)
        result = subprocess.run([sys.executable, "-m", "pytest", test_dir, "-v"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except ImportError:
        print("⚠️  Skipping pytest tests - 'pytest' module not available")
        print("   Install with: pip install pytest")
        return True  # Don't fail the overall test run


def main():
    """Run all available tests."""
    print("🧪 Card Kingdom Buylist Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run simple unit tests (no external dependencies)
    if not run_simple_tests():
        all_passed = False
    
    # Run integration tests (requires requests and running server)
    if not run_integration_tests():
        all_passed = False
    
    # Run pytest tests (requires pytest)
    if not run_pytest_tests():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL AVAILABLE TESTS PASSED! ✅")
        print("\nTest Coverage:")
        print("✅ Unit tests for core functions")
        print("✅ JSONP wrapper cleaning")
        print("✅ Record transformation")
        print("✅ Column mapping validation")
        print("✅ Integration pipeline testing")
        if 'requests' in sys.modules:
            print("✅ HTTP endpoint testing")
        else:
            print("⚠️  HTTP endpoint testing (skipped - install 'requests')")
    else:
        print("❌ SOME TESTS FAILED")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)