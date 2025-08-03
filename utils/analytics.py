# utils/analytics.py
from database import SessionLocal, Statistic, User
from datetime import datetime

def log_event(user_id: int, username: str, event_type: str, test_id: str = None):
    """Логирует событие"""
    session = SessionLocal()
    try:
        # Обновляем или создаём пользователя
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=username,
                first_name=None,
                last_name=None
            )
            session.add(user)
        else:
            user.last_seen = datetime.now()
        
        # Логируем событие
        event = Statistic(
            event_type=event_type,
            user_id=user_id,
            test_id=test_id
        )
        session.add(event)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Ошибка логирования: {e}")
    finally:
        session.close()

def get_stats():
    """Возвращает основную статистику"""
    session = SessionLocal()
    try:
        total_users = session.query(User).count()
        active_users = session.query(User).filter(
            User.last_seen > datetime.now() - timedelta(days=7)
        ).count()
        
        # Топ тестов
        from sqlalchemy import func
        top_tests = session.query(
            Statistic.test_id, 
            func.count(Statistic.id)
        ).filter(
            Statistic.event_type == "test_started"
        ).group_by(Statistic.test_id).order_by(
            func.count(Statistic.id).desc()
        ).limit(5).all()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "top_tests": [{"test_id": t[0], "count": t[1]} for t in top_tests]
        }
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return {}
    finally:
        session.close()