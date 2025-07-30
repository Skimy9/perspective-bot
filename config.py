import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # ID автора бота
    
    # Пути к данным
    DATA_DIR = "data"
    USER_DATA_DIR = "user_data"
    
    # Настройки системы
    DAILY_ACTION_COOLDOWN = 24 * 60 * 60  # 24 часа в секундах
    WEEKLY_REPORT_DAY = 6  # День недели для еженедельного отчета (0 = понедельник, 6 = воскресенье)
    
    # Google Sheets для резервного копирования
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Quantum Compass Backups')
    
    # Проверка обязательных переменных
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set")