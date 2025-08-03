from sqlalchemy.orm import Session
from database.models import User, Question
from database import SessionLocal, engine  # Используем сессию из __init__.py

def save_question(user_id: int, question_text: str):
    """Сохраняет вопрос пользователя в базу данных"""
    with SessionLocal() as session:  # Используем SessionLocal вместо Session(engine)
        # Проверяем существование пользователя
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            # Создаем нового пользователя
            user = User(telegram_id=user_id)
            session.add(user)
            session.commit()
        
        question = Question(user_id=user_id, text=question_text)
        session.add(question)
        session.commit()

def get_user_questions(user_id: int):
    with SessionLocal() as session:
        return session.query(Question).filter(Question.user_id == user_id).all()

def update_question_answer(question_id: int, answer_text: str):
    with SessionLocal() as session:
        question = session.query(Question).get(question_id)
        if question:
            question.answer = answer_text
            question.answered = True
            session.commit()

def get_last_question(user_id: int):
    with SessionLocal() as session:
        return session.query(Question)\
            .filter(Question.user_id == user_id)\
            .order_by(Question.id.desc())\
            .first()