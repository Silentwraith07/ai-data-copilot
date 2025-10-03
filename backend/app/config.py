# Configuration module for environment variables and settings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Centralized configuration for the AI Data Copilot backend.
    Extensible for future cloud storage (Azure Blob, S3) integration.
    """
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Can switch to gpt-4o
    
    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls"}
    
    # Security Configuration
    API_KEY: str = os.getenv("API_KEY", "demo-api-key-change-in-production")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Future: Azure Blob Storage (placeholder for extension)
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    
    def __init__(self):
        # Create upload directory if it doesn't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

settings = Settings()
