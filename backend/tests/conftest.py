"""
Test configuration and fixtures.
"""

import pytest
import os
import sys

# Add the parent directory to the Python path so we can import from main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_card_data():
    """Sample card data for testing."""
    return [
        {
            "i": 10000,
            "n": "Black Lotus",
            "e": "Limited Edition Alpha",
            "r": "R",
            "f": "false",
            "p": "50000.00",
            "q": 1,
            "u": "/images/magic/black-lotus.jpg"
        },
        {
            "i": 10001,
            "n": "Lightning Bolt",
            "e": "Limited Edition Alpha", 
            "r": "C",
            "f": "false",
            "p": "25.00",
            "q": 4,
            "u": "/images/magic/lightning-bolt.jpg"
        }
    ]

@pytest.fixture
def sample_jsonp_data(sample_card_data):
    """Sample JSONP formatted data."""
    import json
    return f'ckCardList({json.dumps(sample_card_data)});'

@pytest.fixture
def transformed_card_data():
    """Expected transformed card data."""
    return [
        {
            "BuyProductId": 10000,
            "BuyCardName": "Black Lotus",
            "BuyEdition": "Limited Edition Alpha",
            "BuyRarity": "R",
            "BuyFoil": "false",
            "BuyPrice": "50000.00",
            "BuyQty": 1,
            "BuyImage": "/images/magic/black-lotus.jpg"
        },
        {
            "BuyProductId": 10001,
            "BuyCardName": "Lightning Bolt",
            "BuyEdition": "Limited Edition Alpha",
            "BuyRarity": "C",
            "BuyFoil": "false",
            "BuyPrice": "25.00",
            "BuyQty": 4,
            "BuyImage": "/images/magic/lightning-bolt.jpg"
        }
    ]