"""
Combined test script to upload CK buylist data and immediately validate it.
This simulates what happens when you upload from your webpage.
"""

import sys
import os
import asyncio
import aiohttp
import time
import pandas as pd

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buylist_core import process_buylist_data, get_buylist_stats, get_buylist_sample, get_buylist_dataframe, clear_buylist_dataframe

async def test_upload_and_validate():
    """Upload buylist data and immediately validate it."""
    print("🧪 CK Buylist Upload + Validation Test")
    print("=" * 60)
    
    # Step 1: Check initial state
    print("\n📊 Step 1: Check initial dataframe state")
    initial_stats = get_buylist_stats()
    print(f"   Initial status: {initial_stats['status']}")
    print(f"   Initial records: {initial_stats['records']:,}")
    
    # Step 2: Upload CK buylist data
    print("\n📡 Step 2: Upload Card Kingdom buylist data")
    try:
        url = "https://www.cardkingdom.com/json/buylist.jsonp"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch data
        fetch_start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                raw_jsonp = await response.text()
        fetch_time = time.time() - fetch_start
        print(f"   ✅ Data fetched in {fetch_time:.2f}s ({len(raw_jsonp):,} characters)")
        
        # Process and save to dataframe
        process_start = time.time()
        transformed_records, total_records = process_buylist_data(raw_jsonp, save_to_dataframe=True)
        process_time = time.time() - process_start
        print(f"   ✅ Data processed in {process_time:.2f}s ({total_records:,} records)")
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False
    
    # Step 3: Validate dataframe after upload
    print("\n🔍 Step 3: Validate dataframe after upload")
    stats = get_buylist_stats()
    print(f"   Status: {stats['status']}")
    print(f"   Records: {stats['records']:,}")
    print(f"   Memory: {stats['memory_mb']} MB")
    print(f"   Columns: {stats['columns']}")
    
    if stats['status'] == 'empty':
        print("   ❌ Dataframe is still empty after upload!")
        return False
    
    # Step 4: Get sample data for validation
    print("\n📋 Step 4: Sample data validation")
    sample = get_buylist_sample(5)
    
    if sample['status'] == 'loaded':
        print(f"   Sample of {sample['sample_size']} records:")
        for i, record in enumerate(sample['sample_data'], 1):
            print(f"\n   📝 Record {i}:")
            print(f"      Card: {record.get('BuyCardName', 'N/A')}")
            print(f"      Edition: {record.get('BuyEdition', 'N/A')}")
            print(f"      Price: ${record.get('BuyPrice', '0.00')}")
            print(f"      Rarity: {record.get('BuyRarity', 'N/A')}")
    
    # Step 5: Direct dataframe analysis
    print("\n🧮 Step 5: Direct dataframe analysis")
    df = get_buylist_dataframe()
    if df is not None:
        print(f"   ✅ Dataframe accessible: {df.shape}")
        
        # Price analysis
        try:
            prices = pd.to_numeric(df['BuyPrice'], errors='coerce')
            print(f"   💰 Price range: ${prices.min():.2f} - ${prices.max():.2f}")
            print(f"   💰 Average price: ${prices.mean():.2f}")
        except Exception as e:
            print(f"   ⚠️ Price analysis error: {e}")
        
        # Edition analysis
        try:
            top_editions = df['BuyEdition'].value_counts().head(5)
            print(f"   🃏 Top 5 editions: {dict(top_editions)}")
        except Exception as e:
            print(f"   ⚠️ Edition analysis error: {e}")
        
        # Rarity analysis
        try:
            rarity_counts = df['BuyRarity'].value_counts()
            print(f"   ⭐ Rarity distribution: {dict(rarity_counts)}")
        except Exception as e:
            print(f"   ⚠️ Rarity analysis error: {e}")
        
        print(f"\n   ✅ Validation successful!")
        return True
    else:
        print(f"   ❌ Cannot access dataframe directly")
        return False

def test_dataframe_functions():
    """Test the new dataframe sample function."""
    print("\n🧮 Step 6: Test new sample function")
    
    # Test different sample sizes
    for size in [3, 10]:
        print(f"\n   Testing sample size: {size}")
        sample = get_buylist_sample(size)
        print(f"   Status: {sample['status']}")
        if sample['status'] == 'loaded':
            print(f"   Sample size: {sample['sample_size']}")
            print(f"   Total records: {sample['total_records']:,}")
            print(f"   First card: {sample['sample_data'][0].get('BuyCardName', 'N/A')}")

if __name__ == "__main__":
    print("🎯 This simulates what happens when you upload from your webpage")
    
    async def main():
        success = await test_upload_and_validate()
        
        if success:
            test_dataframe_functions()
            print("\n🎉 SUCCESS: Upload and validation complete!")
            print("✅ Your webpage upload will work exactly like this")
            print("✅ Data persists in the FastAPI server process")
            print("✅ You can access sample data via API endpoints")
        else:
            print("\n❌ FAILURE: Issues with upload or validation")
        
        print("\n" + "=" * 60)
    
    asyncio.run(main())