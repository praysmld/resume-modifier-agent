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
    
    # LLM Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"
    
    # Session Management
    session_ttl: int = 3600  # 1 hour
    max_session_memory: int = 50  # Maximum messages per session
    
    # PDF Processing
    pdf_directory: str = "./pdf"
    
    # Agent Configuration
    max_iterations: int = 10
    agent_timeout: int = 60
    
    class Config:
        env_file = ".env"


settings = Settings() 