import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 5242880))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)

settings = Settings()