from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # ✅ Все нужные импорты
from telegram.ext import ContextTypes
from config.settings import settings
from keyboards.tests_menu import get_main_inline_keyboard, get_feedback_keyboard, _add_main_menu_button  # ✅ Правильный путь
from database import SessionLocal
from database.models import Question  # ← Эта строка обязательна!
from sqlalchemy.orm import joinedload
from handlers import feedback  # ← Импортируем модуль feedback

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"🔹 Ваш Telegram ID: {user.id}")
    print(f"🔹 ADMIN_ID из настроек: {settings.ADMIN_ID}")
    print(f"🔹 Тип ADMIN_ID: {type(settings.ADMIN_ID)}")
    print(f"🔹 Вы админ? {user.id == settings.ADMIN_ID}")

    is_admin = user.id == settings.ADMIN_ID
    reply_markup = get_main_inline_keyboard(is_admin=is_admin)
    await update.message.reply_text(
        f"Привет, {user.first_name}!\nВыбери действие:",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # Если админ и ожидается ответ — отправляем ответ пользователю
    if user.id == settings.ADMIN_ID and context.user_data.get("admin_waiting_reply"):
        question_id = context.user_data.pop("admin_waiting_reply")

        with SessionLocal() as session:
            question = session.query(Question).options(joinedload(Question.user)).get(question_id)
            if not question:
                await update.message.reply_text("❌ Сообщение не найдено.")
                return

            # Создаём клавиатуру ДО блока try/except
            keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=question.user.telegram_id,
                    text=f"📬 Ответ от автора:\n\n{text}"
                )
                question.answer = text
                question.answered = 1
                session.commit()

                await update.message.reply_text(
                    "✅ Ответ отправлен пользователю.",
                    reply_markup=reply_markup
                )
            except Exception as e:
                session.rollback()
                # Теперь reply_markup точно существует
                await update.message.reply_text(
                    f"❌ Ошибка отправки: {e}",
                    reply_markup=reply_markup
                )
                return

            # 🔁 Показываем обновлённый список непрочитанных
            with SessionLocal() as session:
                unanswered = (
                    session.query(Question)
                    .options(joinedload(Question.user))
                    .filter(Question.answered == 0)
                    .all()
                )

            if not unanswered:
                # ❌ Нет новых сообщений
                keyboard = [[InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "📭 Больше непрочитанных сообщений нет.",
                    reply_markup=reply_markup
                )
            else:
                # 📥 Есть ещё непрочитанные — показываем список
                lines = []
                for q in unanswered:
                    user_obj = q.user
                    user_name = "Пользователь"
                    if user_obj:
                        user_name = f"@{user_obj.username}" if user_obj.username else user_obj.first_name or f"ID {user_obj.telegram_id}"

                    lines.append(
                        f"📩 <b>Сообщение #{q.id}</b>\n"
                        f"👤 От: {user_name}\n"
                        f"💬 {q.text}\n"
                        f"🕒 {q.timestamp.strftime('%H:%M %d.%m')}\n"
                        f"🔹 /reply_{q.id} — ответить"
                    )

                text = "\n\n".join(lines)
                reply_markup = InlineKeyboardMarkup(_add_main_menu_button([]))  # добавляем только кнопку
                await update.message.reply_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
        return

    # Все остальные — обычные пользователи
    await feedback.handle_feedback_message(update, context)

async def handle_author_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Написать автору'"""
    query = update.callback_query
    await query.answer()

    # Показываем клавиатуру с инструкцией
    reply_markup = get_feedback_keyboard()
    await query.edit_message_text(
        text="📩 Отправьте ваше сообщение автору. Я его обязательно прочитаю и постараюсь ответить! Предлагайте новые инструменты или тесты. " \
        "Чего не хватает или что лишнее. Или просто напишите о своих переживаниях.",
        reply_markup=reply_markup
    )