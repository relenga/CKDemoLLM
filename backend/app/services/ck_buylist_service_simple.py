import requests
import json
import re
import logging
from typing import Dict, Any, List
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class CardKingdomBuylistService:
    def __init__(self):
        self.url = "https://www.cardkingdom.com/json/buylist.jsonp"
        self.column_mapping = {
            "i": "BuyProductId",
            "n": "BuyCardName", 
            "e": "BuyEdition",
            "r": "BuyRarity",
            "f": "BuyFoil",
            "p": "BuyPrice",
            "q": "BuyQty",
            "u": "BuyImage"
        }
    
    def _clean_jsonp_response(self, response_text: str) -> str:
        """
        Clean JSONP response by removing the function wrapper
        Expected format: ckCardList([{...}])
        """
        try:
            logger.info(f"Response text length: {len(response_text)}")
            logger.info(f"Response starts with: {response_text[:100] if response_text else 'EMPTY'}")
            
            if not response_text or not response_text.strip():
                raise ValueError("Empty response received")
            
            # Remove the function call wrapper
            # Pattern: functionName([...]) -> [...]
            pattern = r'^[^(]*\((.*)\)$'
            match = re.search(pattern, response_text.strip())
            if match:
                cleaned = match.group(1)
                logger.info(f"Successfully cleaned JSONP, result length: {len(cleaned)}")
                return cleaned
            else:
                # If no wrapper found, assume it's already clean JSON
                logger.warning("No JSONP wrapper found, using response as-is")
                return response_text.strip()
        except Exception as e:
            logger.error(f"Error cleaning JSONP response: {e}")
            raise ValueError(f"Unable to parse JSONP response: {e}")
    
    async def fetch_buylist_data(self) -> Dict[str, Any]:
        """
        Fetch the Card Kingdom buylist data and return as processed dict
        """
        try:
            logger.info("=== STARTING CARD KINGDOM BUYLIST FETCH ===")
            logger.info(f"Target URL: {self.url}")
            
            # Use aiohttp for async HTTP request with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                logger.info("Making HTTP request...")
                async with session.get(self.url) as response:
                    logger.info(f"HTTP Status: {response.status}")
                    logger.info(f"HTTP Reason: {response.reason}")
                    logger.info(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    logger.info(f"Content-Length: {response.headers.get('Content-Length', 'unknown')}")
                    
                    if response.status != 200:
                        response_text = await response.text()
                        logger.error(f"HTTP {response.status}: {response.reason} - {response_text[:500]}")
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    response_text = await response.text()
                    logger.info(f"Received response with length: {len(response_text)} characters")
                    logger.info(f"Response starts with: {response_text[:200] if response_text else 'EMPTY'}")
            
            # Clean the JSONP response
            clean_json = self._clean_jsonp_response(response_text)
            
            # Parse JSON
            logger.info("Parsing JSON data...")
            data = json.loads(clean_json)
            
            if not isinstance(data, list):
                raise ValueError("Expected JSON array format")
            
            logger.info(f"Successfully parsed {len(data)} records")
            
            # Convert column names for first few records as sample
            sample_data = []
            for i, record in enumerate(data[:5]):  # Just first 5 for sample
                converted_record = {}
                for old_key, new_key in self.column_mapping.items():
                    if old_key in record:
                        converted_record[new_key] = record[old_key]
                sample_data.append(converted_record)
            
            logger.info(f"Data processing complete. Total records: {len(data)}")
            
            return {
                "total_records": len(data),
                "sample_records": sample_data,
                "columns": list(self.column_mapping.values()),
                "raw_data": data  # Keep reference to raw data
            }
            
        except Exception as e:
            logger.error(f"Error fetching buylist data: {e}")
            raise Exception(f"Failed to fetch buylist data: {str(e)}")
    
    def get_data_summary(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary statistics of the buylist data
        """
        try:
            summary = {
                "total_records": processed_data["total_records"],
                "columns": processed_data["columns"],
                "memory_usage_mb": len(str(processed_data)) / 1024 / 1024,  # Rough estimate
                "sample_records": processed_data["sample_records"],
                "statistics": {}
            }
            
            # Add some basic statistics from sample data
            if processed_data["sample_records"]:
                summary["statistics"]["sample_analysis"] = {
                    "sample_size": len(processed_data["sample_records"])
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"error": f"Failed to generate summary: {str(e)}"}

# Global instance
ck_buylist_service = CardKingdomBuylistService()