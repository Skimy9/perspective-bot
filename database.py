# database.py
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String(100))
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())

class Statistic(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))  # "start", "test_started", "path_started", "test_completed"
    user_id = Column(Integer)
    test_id = Column(String(50))  # ID теста (например, "big_five")
    timestamp = Column(DateTime, default=func.now())