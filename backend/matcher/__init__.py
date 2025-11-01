"""
Part Matching Engine for CK LangGraph Application
Matches vendor SellList records against Card Kingdom BuyList using TF-IDF similarity
"""

__version__ = "1.0.0"

from .preprocess import create_composite_field, preprocess_dataframe, normalize_text
from .vectorizer import TextVectorizer
from .matcher_core import PartMatcher

__all__ = [
    "create_composite_field",
    "preprocess_dataframe", 
    "normalize_text",
    "TextVectorizer",
    "PartMatcher"
]