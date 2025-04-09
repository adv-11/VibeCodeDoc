import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # GitIngest settings
    GITINGEST_BASE_URL: str = "https://gitingest.com"
    
    # LLM settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    
    # Analysis settings
    MAX_REPO_SIZE_MB: int = 50
    MAX_FILES_TO_ANALYZE: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()