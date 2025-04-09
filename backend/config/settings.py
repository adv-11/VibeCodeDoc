import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Code Analysis API"
    
    # Git settings
    REPO_CLONE_DIR: str = "/tmp/repos"
    
    # LLM settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    
    # Analysis settings
    MAX_FILES_TO_ANALYZE: int = 100
    MAX_FILE_SIZE_KB: int = 500
    ANALYSIS_TIMEOUT_SEC: int = 600  # 10 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()