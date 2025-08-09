# app.py
import os
import logging
from telegram.ext import ApplicationBuilder
from config.settings import settings
from database import init_db
from aiohttp import web

# НАСТРОЙКА ЛОГИРОВАНИЯ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения приложения
application = None

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
    from handlers.tests import setup_handlers
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
