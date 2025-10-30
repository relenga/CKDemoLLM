import pandas as pd
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
    
    async def fetch_buylist_data(self) -> pd.DataFrame:
        """
        Fetch the Card Kingdom buylist data and return as pandas DataFrame
        """
        try:
            logger.info("Starting to fetch Card Kingdom buylist data...")
            
            # Use aiohttp for async HTTP request with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(self.url) as response:
                    logger.info(f"HTTP Status: {response.status}")
                    logger.info(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    
                    if response.status != 200:
                        response_text = await response.text()
                        logger.error(f"HTTP {response.status}: {response.reason} - {response_text[:500]}")
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    response_text = await response.text()
                    logger.info(f"Received response with length: {len(response_text)} characters")
            
            # Clean the JSONP response
            clean_json = self._clean_jsonp_response(response_text)
            
            # Parse JSON
            logger.info("Parsing JSON data...")
            data = json.loads(clean_json)
            
            if not isinstance(data, list):
                raise ValueError("Expected JSON array format")
            
            logger.info(f"Successfully parsed {len(data)} records")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Rename columns according to mapping
            df = df.rename(columns=self.column_mapping)
            
            # Convert data types
            if 'BuyPrice' in df.columns:
                df['BuyPrice'] = pd.to_numeric(df['BuyPrice'], errors='coerce')
            if 'BuyQty' in df.columns:
                df['BuyQty'] = pd.to_numeric(df['BuyQty'], errors='coerce')
            if 'BuyProductId' in df.columns:
                df['BuyProductId'] = pd.to_numeric(df['BuyProductId'], errors='coerce')
            
            # Convert BuyFoil to boolean
            if 'BuyFoil' in df.columns:
                df['BuyFoil'] = df['BuyFoil'].map({'true': True, 'false': False}).fillna(False)
            
            logger.info(f"Data processing complete. Final DataFrame shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching buylist data: {e}")
            raise Exception(f"Failed to fetch buylist data: {str(e)}")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics of the buylist data
        """
        try:
            summary = {
                "total_records": len(df),
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict(),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "sample_records": df.head(5).to_dict('records') if len(df) > 0 else [],
                "statistics": {}
            }
            
            # Add statistics for numeric columns
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                summary["statistics"][col] = {
                    "min": float(df[col].min()) if pd.notna(df[col].min()) else None,
                    "max": float(df[col].max()) if pd.notna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                    "count": int(df[col].count())
                }
            
            # Add value counts for categorical columns
            categorical_columns = ['BuyRarity', 'BuyEdition']
            for col in categorical_columns:
                if col in df.columns:
                    value_counts = df[col].value_counts().head(10)
                    summary["statistics"][f"{col}_top_values"] = value_counts.to_dict()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"error": f"Failed to generate summary: {str(e)}"}

# Global instance
ck_buylist_service = CardKingdomBuylistService()