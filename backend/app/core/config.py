from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "CK LangGraph Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Server settings
    HOST: str = Field(default="localhost", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="BACKEND_CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    
    # LangGraph settings
    LANGGRAPH_CONFIG: dict = {
        "max_iterations": 10,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Database settings (if needed)
    DATABASE_URL: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()