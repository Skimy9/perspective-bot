# database/__init__.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from sqlalchemy.orm import declarative_base

# Создаём Base здесь, чтобы экспортировать
Base = declarative_base()

# Создаём engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=True
)

# Создаём сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Импортируем модели ПОСЛЕ создания Base
from database.models import User, Question, Statistic

# Создаём таблицы
def init_db():
    Base.metadata.create_all(bind=engine)
    print("База данных инициализирована. Таблицы созданы.")