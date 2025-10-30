"""
Unit tests for the Card Kingdom buylist upload functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the main app and functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, fetch_card_kingdom_data
from buylist_core import clean_jsonp_wrapper, transform_record, COLUMN_MAPPING


class TestCleanJSONPWrapper:
    """Test the JSONP wrapper cleaning functionality."""
    
    def test_clean_ck_card_list_wrapper(self):
        """Test cleaning ckCardList([...]) wrapper."""
        raw_data = 'ckCardList([{"i":1,"n":"Test Card"}]);'
        expected = '[{"i":1,"n":"Test Card"}]'
        result = clean_jsonp_wrapper(raw_data)
        assert result == expected
    
    def test_clean_generic_jsonp_wrapper(self):
        """Test cleaning generic JSONP wrapper."""
        raw_data = '([{"i":1,"n":"Test Card"}])'
        expected = '[{"i":1,"n":"Test Card"}]'
        result = clean_jsonp_wrapper(raw_data)
        assert result == expected
    
    def test_no_wrapper_returns_original(self):
        """Test that data without wrapper is returned as-is."""
        raw_data = '[{"i":1,"n":"Test Card"}]'
        result = clean_jsonp_wrapper(raw_data)
        assert result == raw_data
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = clean_jsonp_wrapper("")
        assert result == ""
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        raw_data = '  ckCardList([{"i":1,"n":"Test Card"}]);  '
        expected = '[{"i":1,"n":"Test Card"}]'
        result = clean_jsonp_wrapper(raw_data)
        assert result == expected


class TestTransformRecord:
    """Test the record transformation functionality."""
    
    def test_transform_complete_record(self):
        """Test transforming a record with all fields."""
        input_record = {
            "i": 12345,
            "n": "Black Lotus",
            "e": "Limited Edition Alpha",
            "r": "R",
            "f": "false",
            "p": "50000.00",
            "q": 1,
            "u": "/images/magic/black-lotus.jpg"
        }
        
        expected = {
            "BuyProductId": 12345,
            "BuyCardName": "Black Lotus",
            "BuyEdition": "Limited Edition Alpha",
            "BuyRarity": "R",
            "BuyFoil": "false",
            "BuyPrice": "50000.00",
            "BuyQty": 1,
            "BuyImage": "/images/magic/black-lotus.jpg"
        }
        
        result = transform_record(input_record)
        assert result == expected
    
    def test_transform_partial_record(self):
        """Test transforming a record with missing fields."""
        input_record = {
            "i": 12345,
            "n": "Lightning Bolt",
            "p": "0.50"
        }
        
        expected = {
            "BuyProductId": 12345,
            "BuyCardName": "Lightning Bolt",
            "BuyPrice": "0.50"
        }
        
        result = transform_record(input_record)
        assert result == expected
    
    def test_transform_empty_record(self):
        """Test transforming an empty record."""
        result = transform_record({})
        assert result == {}
    
    def test_transform_unknown_fields_ignored(self):
        """Test that unknown fields are ignored."""
        input_record = {
            "i": 12345,
            "n": "Test Card",
            "unknown_field": "should_be_ignored",
            "another_unknown": 999
        }
        
        expected = {
            "BuyProductId": 12345,
            "BuyCardName": "Test Card"
        }
        
        result = transform_record(input_record)
        assert result == expected


class TestFetchCardKingdomData:
    """Test the Card Kingdom data fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful data fetching."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='ckCardList([{"i":1}]);')
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await fetch_card_kingdom_data()
            assert result == 'ckCardList([{"i":1}]);'
    
    @pytest.mark.asyncio
    async def test_http_error_response(self):
        """Test handling of HTTP error responses."""
        mock_response = Mock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await fetch_card_kingdom_data()
            
            assert exc_info.value.status_code == 404
            assert "Failed to fetch data from Card Kingdom" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_empty_response(self):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='')
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await fetch_card_kingdom_data()
            
            assert exc_info.value.status_code == 500
            assert "Empty response received" in str(exc_info.value.detail)


class TestBuylistUploadEndpoint:
    """Test the main buylist upload endpoint."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    @patch('main.fetch_card_kingdom_data')
    def test_successful_upload(self, mock_fetch):
        """Test successful buylist upload and processing."""
        # Mock the data fetching
        sample_data = 'ckCardList([{"i":1,"n":"Test Card","e":"Test Set","r":"C","f":"false","p":"0.10","q":1,"u":"/test.jpg"}]);'
        mock_fetch.return_value = AsyncMock(return_value=sample_data)
        
        response = self.client.post("/api/buylist/upload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["total_records"] == 1
        assert "processing_time" in data
        assert len(data["sample_records"]) == 1
        assert data["sample_records"][0]["BuyCardName"] == "Test Card"
        assert data["columns"] == list(COLUMN_MAPPING.values())
    
    @patch('main.fetch_card_kingdom_data')
    def test_upload_with_fetch_error(self, mock_fetch):
        """Test upload when data fetching fails."""
        mock_fetch.side_effect = HTTPException(status_code=500, detail="Network error")
        
        response = self.client.post("/api/buylist/upload")
        
        assert response.status_code == 500
        assert "Network error" in response.json()["detail"]
    
    @patch('main.fetch_card_kingdom_data')
    def test_upload_with_invalid_json(self, mock_fetch):
        """Test upload with invalid JSON data."""
        mock_fetch.return_value = AsyncMock(return_value='ckCardList([invalid json]);')
        
        response = self.client.post("/api/buylist/upload")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to parse JSON data" in data["detail"]
    
    @patch('main.fetch_card_kingdom_data')
    def test_upload_with_multiple_records(self, mock_fetch):
        """Test upload with multiple records."""
        sample_data = '''ckCardList([
            {"i":1,"n":"Card One","e":"Set One","r":"C","f":"false","p":"0.10","q":1,"u":"/card1.jpg"},
            {"i":2,"n":"Card Two","e":"Set Two","r":"U","f":"true","p":"0.25","q":2,"u":"/card2.jpg"},
            {"i":3,"n":"Card Three","e":"Set Three","r":"R","f":"false","p":"1.00","q":0,"u":"/card3.jpg"}
        ]);'''
        mock_fetch.return_value = AsyncMock(return_value=sample_data)
        
        response = self.client.post("/api/buylist/upload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["total_records"] == 3
        assert len(data["sample_records"]) == 3
        
        # Check that transformation worked correctly
        assert data["sample_records"][0]["BuyCardName"] == "Card One"
        assert data["sample_records"][1]["BuyCardName"] == "Card Two"
        assert data["sample_records"][2]["BuyCardName"] == "Card Three"
    
    @patch('main.fetch_card_kingdom_data')
    def test_upload_with_large_dataset(self, mock_fetch):
        """Test upload with large dataset (sample size limit)."""
        # Create a dataset with 10 records
        records = []
        for i in range(10):
            records.append({
                "i": i,
                "n": f"Card {i}",
                "e": f"Set {i}",
                "r": "C",
                "f": "false",
                "p": "0.10",
                "q": 1,
                "u": f"/card{i}.jpg"
            })
        
        sample_data = f'ckCardList({json.dumps(records)});'
        mock_fetch.return_value = AsyncMock(return_value=sample_data)
        
        response = self.client.post("/api/buylist/upload")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["total_records"] == 10
        # Should only return 5 sample records due to limit
        assert len(data["sample_records"]) == 5


class TestAPIEndpoints:
    """Test basic API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "CK LangGraph Backend API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_test_endpoint(self):
        """Test the API test endpoint."""
        response = self.client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test endpoint is working!"
        assert data["status"] == "ok"
    
    def test_buylist_test_endpoint(self):
        """Test the buylist test endpoint."""
        response = self.client.get("/api/buylist/test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Buylist endpoint is registered!"
        assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])