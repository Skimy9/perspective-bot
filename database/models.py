# database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base  # ← Теперь это работает, потому что Base определён в __init__.py

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")
    statistics = relationship("Statistic", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    answered = Column(Integer, default=0)
    answer = Column(Text, nullable=True)
    answer_timestamp = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="questions")


class Statistic(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    test_id = Column(String(50), nullable=True)
    stage = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="statistics")