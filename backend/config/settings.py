import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Code Refactoring Advisor"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]
    
    # LLM settings
    LLM_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-turbo")
    
    # GitHub API settings
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    
    # Application settings
    MAX_ANALYSIS_THREADS: int = 4
    MAX_FILE_SIZE_KB: int = 500
    MAX_FILES_PER_REPO: int = 50
    SUPPORTED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", 
        ".c", ".cpp", ".cs", ".go", ".rb", ".php"
    ]
    
    # Database settings (if needed)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Redis settings (for caching)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        case_sensitive = True

# Create settings instance
settings = Settings()