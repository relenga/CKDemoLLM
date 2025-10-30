"""
Simple unit tests for the Card Kingdom buylist upload functionality.
Can be run without pytest - just execute: python test_buylist_simple.py
"""

import json
import sys
import os

# Add the parent directory to the Python path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from buylist_core import clean_jsonp_wrapper, transform_record, COLUMN_MAPPING, process_buylist_data
    print("✅ Successfully imported functions from buylist_core.py")
except ImportError as e:
    print(f"❌ Failed to import from buylist_core.py: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def test_clean_jsonp_wrapper():
    """Test the JSONP wrapper cleaning functionality."""
    print("\n🧪 Testing clean_jsonp_wrapper...")
    
    # Test 1: Clean ckCardList wrapper
    test_data_1 = 'ckCardList([{"i":1,"n":"Test Card"}]);'
    expected_1 = '[{"i":1,"n":"Test Card"}]'
    result_1 = clean_jsonp_wrapper(test_data_1)
    assert result_1 == expected_1, f"Expected {expected_1}, got {result_1}"
    print("✅ ckCardList wrapper cleaning works")
    
    # Test 2: Generic JSONP wrapper
    test_data_2 = '([{"i":1,"n":"Test Card"}])'
    expected_2 = '[{"i":1,"n":"Test Card"}]'
    result_2 = clean_jsonp_wrapper(test_data_2)
    assert result_2 == expected_2, f"Expected {expected_2}, got {result_2}"
    print("✅ Generic JSONP wrapper cleaning works")
    
    # Test 3: No wrapper
    test_data_3 = '[{"i":1,"n":"Test Card"}]'
    result_3 = clean_jsonp_wrapper(test_data_3)
    assert result_3 == test_data_3, f"Expected {test_data_3}, got {result_3}"
    print("✅ No wrapper handling works")
    
    # Test 4: Empty string
    result_4 = clean_jsonp_wrapper("")
    assert result_4 == "", f"Expected empty string, got {result_4}"
    print("✅ Empty string handling works")
    
    print("✅ All clean_jsonp_wrapper tests passed!")


def test_transform_record():
    """Test the record transformation functionality."""
    print("\n🧪 Testing transform_record...")
    
    # Test 1: Complete record
    input_record_1 = {
        "i": 12345,
        "n": "Black Lotus",
        "e": "Limited Edition Alpha",
        "r": "R",
        "f": "false",
        "p": "50000.00",
        "q": 1,
        "u": "/images/magic/black-lotus.jpg"
    }
    
    expected_1 = {
        "BuyProductId": 12345,
        "BuyCardName": "Black Lotus",
        "BuyEdition": "Limited Edition Alpha",
        "BuyRarity": "R",
        "BuyFoil": "false",
        "BuyPrice": "50000.00",
        "BuyQty": 1,
        "BuyImage": "/images/magic/black-lotus.jpg"
    }
    
    result_1 = transform_record(input_record_1)
    assert result_1 == expected_1, f"Expected {expected_1}, got {result_1}"
    print("✅ Complete record transformation works")
    
    # Test 2: Partial record
    input_record_2 = {
        "i": 12345,
        "n": "Lightning Bolt",
        "p": "0.50"
    }
    
    expected_2 = {
        "BuyProductId": 12345,
        "BuyCardName": "Lightning Bolt",
        "BuyPrice": "0.50"
    }
    
    result_2 = transform_record(input_record_2)
    assert result_2 == expected_2, f"Expected {expected_2}, got {result_2}"
    print("✅ Partial record transformation works")
    
    # Test 3: Empty record
    result_3 = transform_record({})
    assert result_3 == {}, f"Expected empty dict, got {result_3}"
    print("✅ Empty record transformation works")
    
    # Test 4: Unknown fields ignored
    input_record_4 = {
        "i": 12345,
        "n": "Test Card",
        "unknown_field": "should_be_ignored",
        "another_unknown": 999
    }
    
    expected_4 = {
        "BuyProductId": 12345,
        "BuyCardName": "Test Card"
    }
    
    result_4 = transform_record(input_record_4)
    assert result_4 == expected_4, f"Expected {expected_4}, got {result_4}"
    print("✅ Unknown fields filtering works")
    
    print("✅ All transform_record tests passed!")


def test_column_mapping():
    """Test that the column mapping is correct."""
    print("\n🧪 Testing COLUMN_MAPPING...")
    
    expected_mapping = {
        "i": "BuyProductId",
        "n": "BuyCardName", 
        "e": "BuyEdition",
        "r": "BuyRarity",
        "f": "BuyFoil",
        "p": "BuyPrice",
        "q": "BuyQty",
        "u": "BuyImage"
    }
    
    assert COLUMN_MAPPING == expected_mapping, f"Column mapping mismatch: {COLUMN_MAPPING}"
    print("✅ Column mapping is correct")
    print(f"   Columns: {list(COLUMN_MAPPING.keys())} -> {list(COLUMN_MAPPING.values())}")


def test_process_buylist_data():
    """Test the complete buylist data processing function."""
    print("\n🧪 Testing process_buylist_data...")
    
    # Test with single record
    raw_jsonp = 'ckCardList([{"i":10000,"n":"Black Lotus","e":"Limited Edition Alpha","r":"R","f":"false","p":"50000.00","q":1,"u":"/images/magic/black-lotus.jpg"}]);'
    
    try:
        transformed_records, total_count = process_buylist_data(raw_jsonp)
        
        assert total_count == 1, f"Expected 1 record, got {total_count}"
        assert len(transformed_records) == 1, f"Expected 1 transformed record, got {len(transformed_records)}"
        
        # Check transformation
        record = transformed_records[0]
        assert record["BuyCardName"] == "Black Lotus", f"Expected 'Black Lotus', got {record.get('BuyCardName')}"
        assert record["BuyProductId"] == 10000, f"Expected 10000, got {record.get('BuyProductId')}"
        
        print("✅ Single record processing works")
        
    except Exception as e:
        raise AssertionError(f"process_buylist_data failed: {e}")
    
    # Test with multiple records
    multi_record_jsonp = 'ckCardList([{"i":1,"n":"Card One","p":"1.00"},{"i":2,"n":"Card Two","p":"2.00"}]);'
    
    try:
        transformed_records, total_count = process_buylist_data(multi_record_jsonp)
        
        assert total_count == 2, f"Expected 2 records, got {total_count}"
        assert len(transformed_records) == 2, f"Expected 2 transformed records, got {len(transformed_records)}"
        assert transformed_records[0]["BuyCardName"] == "Card One"
        assert transformed_records[1]["BuyCardName"] == "Card Two"
        
        print("✅ Multiple record processing works")
        
    except Exception as e:
        raise AssertionError(f"Multi-record processing failed: {e}")
    
    print("✅ All process_buylist_data tests passed!")


def test_integration_scenario():
    """Test a full integration scenario."""
    print("\n🧪 Testing integration scenario...")
    
    # Simulate full processing pipeline
    raw_jsonp = 'ckCardList([{"i":10000,"n":"Black Lotus","e":"Limited Edition Alpha","r":"R","f":"false","p":"50000.00","q":1,"u":"/images/magic/black-lotus.jpg"}]);'
    
    # Use the new integrated function
    try:
        transformed_records, total_count = process_buylist_data(raw_jsonp)
        
        print(f"✅ Processed {total_count} records successfully")
        print(f"✅ Transformed {len(transformed_records)} records")
        
        # Verify transformation
        expected_card_name = "Black Lotus"
        actual_card_name = transformed_records[0]["BuyCardName"]
        assert actual_card_name == expected_card_name, f"Expected {expected_card_name}, got {actual_card_name}"
        
        print("✅ Integration scenario completed successfully!")
        print(f"   Sample transformed record: {transformed_records[0]}")
        
    except Exception as e:
        raise AssertionError(f"Integration test failed: {e}")


def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Card Kingdom Buylist Upload Tests")
    print("=" * 60)
    
    try:
        test_column_mapping()
        test_clean_jsonp_wrapper()
        test_transform_record()
        test_process_buylist_data()
        test_integration_scenario()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! ✅")
        print("\nThe Card Kingdom buylist upload functionality is working correctly:")
        print("✅ JSONP wrapper cleaning")
        print("✅ Record transformation") 
        print("✅ Column mapping")
        print("✅ Full integration pipeline")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)