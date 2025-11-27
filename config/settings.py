
import os
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

class Settings:
    """Configurazione applicazione"""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    #ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # LLM Config
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini/gemini-2.0-flash")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Letta AI Config
    LETTA_BASE_URL: str = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    LETTA_SERVER_URL: str = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    LETTA_API_KEY: str = os.getenv("LETTA_API_KEY", "")  # Opzionale per server locale
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medical_ai.db")
    
    # Sicurezza
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    PIN_LENGTH: int = 6
    MAX_LOGIN_ATTEMPTS: int = 3
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Crew Config
    CREW_VERBOSE: bool = os.getenv("CREW_VERBOSE", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Valida configurazione"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY mancante nel file .env")
        # Letta è opzionale in fase di sviluppo
        return True

settings = Settings()