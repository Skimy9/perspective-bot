import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')

settings = Settings()