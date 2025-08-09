# app.py
import os
import logging
from telegram.ext import ApplicationBuilder
from config.settings import settings
from database import init_db
from aiohttp import web
import handlers.nagual_journey as nagual_journey
import handlers.tests as tests
import handlers.admin as admin
import handlers.common as common
import handlers.feedback as feedback
from handlers.admin import admin_show_unanswered, handle_admin_reply_command

# НАСТРОЙКА ЛОГИРОВАНИЯ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения приложения
application = None

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
    app.add_handler(CallbackQueryHandler(admin.show_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(nagual_journey.start_nagual_journey, pattern="^nagual_intro$"))
    
    # 2. Команды
    app.add_handler(CommandHandler("start", common.start))

    # 3. Сообщения
    app.add_handler(MessageHandler(
        filters.COMMAND & filters.User(user_id=settings.ADMIN_ID),
        handle_admin_reply_command
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, common.handle_message))

async def setup_application():
    """Настройка приложения бота"""
    global application
    
    # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ — САМАЯ ПЕРВАЯ ОПЕРАЦИЯ
    init_db()
    
    # Создание приложения
    application = ApplicationBuilder() \
        .token(settings.BOT_TOKEN) \
        .connect_timeout(30) \
        .read_timeout(30) \
        .pool_timeout(30) \
        .build()
    
    # Настройка обработчиков
    setup_handlers(application)
    
    # Инициализация приложения
    await application.initialize()
    
    return application

async def handle_webhook(request):
    """Обработчик входящих вебхуков от Telegram"""
    try:
        update = await request.json()
        await application.process_update(Update.de_json(update, application.bot))
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(status=500)

async def on_startup(app):
    """Действия при запуске приложения"""
    # Настройка приложения
    bot_app = await setup_application()
    
    # Получение порта
    port = int(os.environ.get('PORT', '10000'))
    
    # Определение домена
    domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'perspective-bot.onrender.com')
    webhook_url = f"https://{domain}/webhook"
    
    logger.info(f"🌍 Устанавливаю вебхук: {webhook_url}")
    
    # Удаление текущего вебхука
    await bot_app.bot.delete_webhook(drop_pending_updates=True)
    
    # Регистрация вебхука в Telegram
    await bot_app.bot.set_webhook(
        url=webhook_url,
        secret_token=os.environ.get('WEBHOOK_SECRET', 'YOUR_SECRET_TOKEN'),
        allowed_updates=["message", "callback_query"]
    )
    
    # Запуск приложения бота
    await bot_app.start()
    
    logger.info(f"✅ Бот запущен с увеличенными таймаутами")

async def on_shutdown(app):
    """Действия при остановке приложения"""
    global application
    if application:
        await application.stop()
        await application.shutdown()

def create_app():
    """Создание и настройка приложения aiohttp"""
    app = web.Application()
    
    # Добавление обработчика вебхуков
    app.router.add_post('/webhook', handle_webhook)
    
    # Добавление хуков для запуска и остановки
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app

if __name__ == "__main__":
    logger.info("База данных инициализирована. Таблицы созданы.")
    web.run_app(create_app(), host='0.0.0.0', port=int(os.environ.get('PORT', '10000')))
