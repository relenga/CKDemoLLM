"""
Quick validation script to check the dataframe after webpage upload.
Run this after uploading buylist data from your webpage.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buylist_core import get_buylist_stats, get_buylist_sample, get_buylist_dataframe

def validate_dataframe():
    """Validate the current dataframe and show sample data."""
    print("🔍 Buylist Dataframe Validation")
    print("=" * 50)
    
    # Get basic stats
    stats = get_buylist_stats()
    print(f"\n📊 Dataframe Statistics:")
    print(f"   Status: {stats['status']}")
    
    if stats['status'] == 'empty':
        print("   ❌ No data found in dataframe")
        print("   💡 Please upload buylist data from your webpage first")
        return False
    
    print(f"   Records: {stats['records']:,}")
    print(f"   Memory: {stats['memory_mb']} MB")
    print(f"   Columns: {stats['columns']}")
    
    # Get sample data
    print(f"\n📋 Sample Data (first 5 records):")
    sample = get_buylist_sample(5)
    
    if sample['status'] == 'loaded':
        for i, record in enumerate(sample['sample_data'], 1):
            print(f"\n   Record {i}:")
            for key, value in record.items():
                print(f"      {key}: {value}")
    
    # Get direct dataframe access for additional validation
    df = get_buylist_dataframe()
    if df is not None:
        print(f"\n🔍 Additional Validation:")
        print(f"   Dataframe shape: {df.shape}")
        print(f"   Data types: {dict(df.dtypes)}")
        
        # Show some statistics
        if 'BuyPrice' in df.columns:
            try:
                import pandas as pd
                prices = pd.to_numeric(df['BuyPrice'], errors='coerce')
                print(f"   Price range: ${prices.min():.2f} - ${prices.max():.2f}")
                print(f"   Average price: ${prices.mean():.2f}")
            except:
                print(f"   Price column: {df['BuyPrice'].dtype}")
        
        if 'BuyEdition' in df.columns:
            top_editions = df['BuyEdition'].value_counts().head(3)
            print(f"   Top 3 editions: {dict(top_editions)}")
        
        print(f"\n✅ Dataframe validation complete!")
        print(f"✅ {len(df):,} records are accessible and valid")
        return True
    else:
        print(f"   ❌ Could not access dataframe directly")
        return False

if __name__ == "__main__":
    print("🧪 Running dataframe validation...")
    success = validate_dataframe()
    
    if success:
        print(f"\n🎉 SUCCESS: Your dataframe is loaded and accessible!")
        print(f"✅ You can now use the data for analysis")
    else:
        print(f"\n❌ ISSUE: Dataframe validation failed")
        print(f"💡 Try uploading buylist data from your webpage first")
    
    print(f"\n" + "=" * 50)