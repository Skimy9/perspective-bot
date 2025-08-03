from telegram import Update
from telegram.ext import ContextTypes
from database.crud import save_question
from config.settings import settings
import logging
from telegram import InlineKeyboardMarkup
from keyboards.tests_menu import _add_main_menu_button


logger = logging.getLogger(__name__)

async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text

    # Сохраняем вопрос
    try:
        save_question(user.id, message)
        logger.info(f"Сообщение сохранено в базу данных")
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await update.message.reply_text("❌ Ошибка сохранения сообщения.")
        return

    # Отправляем уведомление админу
    try:
        await context.bot.send_message(
            chat_id=settings.ADMIN_ID,
            text=f"📬 Новое сообщение от {user.full_name} (ID: {user.id}):\n\n{message}"
        )
        logger.info("Сообщение успешно отправлено админу")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение админу: {e}")

    await update.message.reply_text(
        "✅ Ваше сообщение отправлено автору!",
        reply_markup=InlineKeyboardMarkup(_add_main_menu_button([]))
    )