# app.py
import logging
import handlers.nagual_journey as nagual_journey
import handlers.tests as tests
import handlers.admin as admin

# НАСТРОЙКА ЛОГИРОВАНИЯ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Меняйте на DEBUG при отладке
)

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.settings import settings
import handlers.common as common
import handlers.feedback as feedback
from handlers.admin import admin_show_unanswered, handle_admin_reply_command
from database import init_db  # ← Добавлен импорт для инициализации БД

logger = logging.getLogger(__name__)


def setup_handlers(app):
    """Настройка обработчиков бота"""
    # 1. Самые специфичные паттерны — в начало
    app.add_handler(CallbackQueryHandler(tests.handle_answer, pattern="^answer_"))          # answer_0_1
    app.add_handler(CallbackQueryHandler(tests.handle_test_action, pattern="^test_"))       # test_soul_type
    app.add_handler(CallbackQueryHandler(tests.handle_category_action, pattern="^category_"))  # category_esoteric
    app.add_handler(CallbackQueryHandler(tests.handle_main_menu_action, pattern="^(show_categories|to_main)$"))
    app.add_handler(CallbackQueryHandler(common.handle_author_message, pattern="^ask_author$"))
    app.add_handler(CallbackQueryHandler(admin_show_unanswered, pattern="^admin_unanswered$"))
    app.add_handler(CallbackQueryHandler(nagual_journey.start_nagual_journey, pattern="^nagual_intro$"))
    app.add_handler(CallbackQueryHandler(nagual_journey.handle_nagual_action, pattern="^nagual:"))
    app.add_handler(CallbackQueryHandler(admin_show_unanswered, pattern="^admin_unanswered$"))
    app.add_handler(CallbackQueryHandler(admin.show_stats, pattern="^admin_stats$"))  # ← Добавьте эту строку
    app.add_handler(CallbackQueryHandler(nagual_journey.start_nagual_journey, pattern="^nagual_intro$"))
    # 2. Команды
    app.add_handler(CommandHandler("start", common.start))

    # 3. Сообщения
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.User(user_id=settings.ADMIN_ID),
        handle_admin_reply_command
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, common.handle_message))


def main():
    try:
        # ✅ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ — САМАЯ ПЕРВАЯ ОПЕРАЦИЯ
        init_db()

        # Создание приложения
        app = ApplicationBuilder() \
            .token(settings.BOT_TOKEN) \
            .connect_timeout(30) \
            .read_timeout(30) \
            .pool_timeout(30) \
            .build()

        setup_handlers(app)
        logger.info("✅ Бот запущен с увеличенными таймаутами")
        app.run_polling()
    except Exception as e:
        logger.critical(f"❌ Ошибка запуска бота: {e}", exc_info=True)


if __name__ == "__main__":
    main()