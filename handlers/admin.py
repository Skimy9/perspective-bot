# admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import settings
from database import SessionLocal
from database.models import Question, User, Statistic
from sqlalchemy.orm import joinedload
import logging
from sqlalchemy import func
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику бота (только для админа)"""
    if update.effective_user.id != settings.ADMIN_ID:
        return

    query = update.callback_query
    if query:
        await query.answer()

    # ✅ Исправлено: используем Python для расчёта даты
    seven_days_ago = datetime.now() - timedelta(days=7)

    with SessionLocal() as session:
        total_users = session.query(User).count()
        
        # ✅ Исправлено: сравниваем с реальной датой
        active_users = session.query(User).filter(
            User.last_seen > seven_days_ago
        ).count()

        # Топ тестов
        top_tests = session.query(
            Statistic.test_id,
            func.count(Statistic.id)
        ).filter(
            Statistic.event_type == "test_started"
        ).group_by(
            Statistic.test_id
        ).order_by(
            func.count(Statistic.id).desc()
        ).limit(5).all()

        # Активность по "Пути к Скрытому"
        path_started = session.query(func.count(Statistic.id)).filter(
            Statistic.event_type == "path_started"
        ).scalar()

        path_completed = session.query(func.count(Statistic.id)).filter(
            Statistic.event_type == "path_completed"
        ).scalar()

    # Формируем сообщение
    test_names = {
        "big_five": "Big Five",
        "depression": "Тест на депрессию",
        "path_to_hidden": "Путь к Скрытому"
    }

    top_tests_text = "\n".join([
        f"  {i+1}. {test_names.get(t[0], t[0])} — {t[1]} запусков"
        for i, t in enumerate(top_tests)
    ]) or "  Нет данных"

    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 <b>Всего пользователей:</b> {total_users}\n"
        f"🟢 <b>Активных (за 7 дней):</b> {active_users}\n\n"
        f"🌀 <b>Путь к Скрытому:</b>\n"
        f"  Запущено: {path_started}\n"
        f"  Пройдено: {path_completed}\n\n"
        f"🎯 <b>ТОП тестов:</b>\n{top_tests_text}"
    )

    # Кнопка "Обновить"
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query and query.message:
        await query.edit_message_text(
            text=stats_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text=stats_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


async def admin_show_unanswered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все неотвеченные сообщения пользователей"""
    query = update.callback_query
    await query.answer()

    try:
        with SessionLocal() as session:
            unanswered = (
                session.query(Question)
                .options(joinedload(Question.user))
                .filter(Question.answered == 0)
                .order_by(Question.timestamp.asc())
                .all()
            )

        if not unanswered:
            keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="📭 Нет новых сообщений.",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            return

        lines = []
        for q in unanswered:
            user_obj: User = q.user
            if user_obj:
                user_name = f"@{user_obj.username}" if user_obj.username else user_obj.first_name or f"ID {user_obj.telegram_id}"
            else:
                user_name = "Неизвестный пользователь"

            lines.append(
                f"📩 <b>Сообщение #{q.id}</b>\n"
                f"👤 От: {user_name}\n"
                f"💬 {q.text[:100]}{'...' if len(q.text) > 100 else ''}\n"
                f"🕒 {q.timestamp.strftime('%H:%M %d.%m')}\n"
                f"🔹 /reply_{q.id} — ответить"
            )

        text = "\n\n".join(lines)
        keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при отображении неотвеченных сообщений: {e}", exc_info=True)
        await query.edit_message_text(
            text="❌ Произошла ошибка при загрузке сообщений.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]])
        )


async def handle_admin_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /reply_X — начало ответа на сообщение"""
    user = update.effective_user
    if user.id != settings.ADMIN_ID:
        logger.warning(f"Попытка доступа к админ-команде от пользователя {user.id}")
        return

    message = update.message.text.strip()
    if not message.startswith("/reply_"):
        return

    try:
        question_id = int(message.split("_", 1)[1])  # Защита от пустых значений
        context.user_data["admin_waiting_reply"] = question_id

        logger.info(f"Админ {user.id} начал отвечать на сообщение #{question_id}")

        await update.message.reply_text(
            f"✏️ Введите ответ на сообщение <b>#{question_id}</b>. Он будет отправлен пользователю.",
            parse_mode="HTML"
        )
    except (IndexError, ValueError) as e:
        logger.warning(f"Неверный формат команды /reply_: {message}")
        await update.message.reply_text("❌ Неверный формат команды. Пример: /reply_123")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /reply_: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при обработке команды.")