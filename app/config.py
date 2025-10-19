import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Resume Modifier Backend"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please")
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # LLM Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_email: Optional[str] = None
    supabase_password: Optional[str] = None

    # Session Management
    session_ttl: int = 3600  # 1 hour
    max_session_memory: int = 50  # Maximum messages per session
    
    # PDF Processing
    pdf_directory: str = "./pdf"
    cv_directory: str = "./cv"
    output_directory: str = "./output"
    
    # Agent Configuration
    max_iterations: int = 10
    agent_timeout: int = 60
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    
    # Rate Limiting
    rate_limit_modify_resume: int = 10  # per hour
    rate_limit_quick_modify: int = 20  # per hour
    rate_limit_general: int = 100  # per hour
    
    class Config:
        env_file = ".env"


settings = Settings() 