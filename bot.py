import os
import json
import logging
from flask import Flask, request
import telebot
from telebot import types

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Приветственное сообщение
WELCOME_MESSAGE = """
🌌 *Добро пожаловать в Квантовый Компас*

Здесь вы найдете не просто вопросы и рекомендации, а персональный путь к осознанию ваших скрытых ресурсов.

Вы не одиноки в своих поисках. Здесь вас понимают, здесь вас принимают таким, какой вы есть.

Нажмите /start, чтобы начать свое путешествие к новому пониманию себя.

⚠️ *Важно знать*
Квантовый Компас — это инструмент для саморефлексии и личного роста, а не замена профессиональной психологической помощи. Результаты не являются диагнозом. Если вы переживаете серьезные трудности, пожалуйста, обратитесь к квалифицированному специалисту.
"""

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info(f"Пользователь {message.chat.id} запустил бота")
    
    # Отправляем приветствие
    bot.reply_to(
        message, 
        WELCOME_MESSAGE,
        parse_mode='Markdown'
    )
    
    # Добавляем кнопку для начала
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Начать работу")
    btn2 = types.KeyboardButton("Задать вопрос автору")
    markup.add(btn1, btn2)
    
    bot.send_message(
        message.chat.id,
        "Готовы начать свое путешествие к осознанности?",
        reply_markup=markup
    )

# ОСНОВНАЯ ПРАВКА: Добавляем логирование в начало обработчика /myid
@bot.message_handler(commands=['myid'])
def get_my_id(message):
    logger.info(f"!!! ОБРАБОТЧИК /myid ВЫЗВАН ДЛЯ ПОЛЬЗОВАТЕЛЯ {message.chat.id} !!!")
    
    try:
        logger.info(f"Пользователь {message.chat.id} запросил свой ID")
        
        bot.reply_to(
            message,
            f"Ваш Telegram ID: `{message.chat.id}`\n\n"
            "Скопируйте это число и вставьте в .env файл как ADMIN_ID, "
            "если вы являетесь автором этого бота.",
            parse_mode='Markdown'
        )
        logger.info("Сообщение с ID успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка при обработке /myid: {str(e)}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")

# Обработчик для кнопки "Начать работу"
@bot.message_handler(func=lambda message: message.text == "Начать работа")
def start_work(message):
    logger.info(f"Пользователь {message.chat.id} начал работу")
    
    # Здесь будет логика начала работы с ботом
    bot.reply_to(
        message,
        "✨ *Начало работы*\n\n"
        "Спасибо, что решили начать свое путешествие!\n\n"
        "Для начала рекомендуем пройти несколько коротких тестов, "
        "чтобы мы могли лучше понять вашу ситуацию и дать персонализированные рекомендации.\n\n"
        "Нажмите /test, чтобы выбрать тест для прохождения.",
        parse_mode='Markdown'
    )

# Обработчик для кнопки "Задать вопрос автору"
@bot.message_handler(func=lambda message: message.text == "Задать вопрос автору")
def ask_question(message):
    logger.info(f"Пользователь {message.chat.id} хочет задать вопрос автору")
    
    bot.reply_to(
        message,
        "✍️ *Задайте ваш вопрос*\n\n"
        "Напишите сообщение, и оно будет отправлено автору бота. "
        "Мы постараемся ответить в ближайшее время.",
        parse_mode='Markdown'
    )

# КРИТИЧЕСКАЯ ПРАВКА: Изменен обработчик для всех сообщений
# Теперь он НЕ перехватывает команды
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def echo_all(message):
    logger.info(f"Пользователь {message.chat.id} отправил сообщение: {message.text}")
    
    # Для примера, просто повторяем сообщение
    bot.reply_to(
        message, 
        "Спасибо за ваше сообщение! В настоящее время мы работаем над функционалом бота. "
        "Попробуйте использовать команду /start для начала работы."
    )

# Инициализация Flask приложения для вебхуков
app = Flask(__name__)

# Маршрут для вебхуков
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    logger.info("Получен запрос от Telegram")
    try:
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        logger.info("Обновление обработано успешно")
        return "!", 200
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {str(e)}")
        return "Error", 500

# КРИТИЧЕСКАЯ ПРАВКА: Отдельный маршрут для установки вебхука
@app.route("/setup_webhook", methods=['GET'])
def setup_webhook():
    logger.info("Запрошена установка вебхука")
    
    # УДАЛЯЕМ СУЩЕСТВУЮЩИЙ ВЕБХУК
    bot.remove_webhook()
    
    # Формируем URL для вебхука
    service_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if service_url:
        webhook_url = f"https://{service_url}/{BOT_TOKEN}"
    else:
        # ЗАМЕНИТЕ 'quantum-compass' НА ИМЯ ВАШЕГО СЕРВИСА В RENDER
        webhook_url = f"https://quantum-compass.onrender.com/{BOT_TOKEN}"
    
    logger.info(f"Устанавливаем вебхук: {webhook_url}")
    result = bot.set_webhook(url=webhook_url)
    
    if result:
        return f"Webhook setup complete to {webhook_url}", 200
    else:
        return "Webhook setup failed", 500

# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    
    # Получаем порт из переменной окружения
    port = int(os.environ.get('PORT', 10000))
    
    # Запускаем Flask на 0.0.0.0
    app.run(host="0.0.0.0", port=port)
