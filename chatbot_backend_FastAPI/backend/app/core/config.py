from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str 
    
    # AI/ML Configuration
    HUGGINGFACE_TOKEN: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: Optional[str] = "rag-chatbot-project"
    
    # Authentication
    JWT_SECRET_KEY: Optional[str] = "supersecretkey"
    JWT_ALGORITHM: Optional[str] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = 10080
    
    # GitHub Integration (Optional)
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_CODESPACE_TOKEN: Optional[str] = None
    
    # Application
    ENVIRONMENT: Optional[str] = "development"
    HOST: Optional[str] = "0.0.0.0"
    PORT: Optional[int] = 8000
    DEBUG: Optional[bool] = True
    RELOAD: Optional[bool] = True
    
    # CORS
    ALLOWED_ORIGINS: Optional[str] = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Vector Database
    CHROMA_PERSIST_DIRECTORY: Optional[str] = "./chroma_db"
    CHROMA_COLLECTION_NAME: Optional[str] = "documents"
    
    # File Upload
    MAX_FILE_SIZE: Optional[int] = 10485760  # 10MB
    ALLOWED_EXTENSIONS: Optional[str] = "pdf"
    UPLOAD_DIR: Optional[str] = "./uploads"
    
    # Logging
    LOG_LEVEL: Optional[str] = "INFO"

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".env")
        case_sensitive = True

settings = Settings()
