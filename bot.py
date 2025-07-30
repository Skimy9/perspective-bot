import os
import time
import json
import logging
from datetime import datetime

import telebot
from telebot import types
from flask import Flask, request

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

# Инициализация Flask приложения для вебхуков
app = Flask(__name__)

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

# Обработчик команды /myid
@bot.message_handler(commands=['myid'])
def get_my_id(message):
    logger.info(f"Пользователь {message.chat.id} запросил свой ID")
    
    bot.reply_to(
        message,
        f"Ваш Telegram ID: `{message.chat.id}`\n\n"
        "Скопируйте это число и вставьте в .env файл как ADMIN_ID, "
        "если вы являетесь автором этого бота.",
        parse_mode='Markdown'
    )

# Обработчик для кнопки "Начать работу"
@bot.message_handler(func=lambda message: message.text == "Начать работу")
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
    # Здесь можно добавить логику ожидания вопроса

# Обработчик для всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"Пользователь {message.chat.id} отправил сообщение: {message.text}")
    
    # Для примера, просто повторяем сообщение
    bot.reply_to(
        message, 
        "Спасибо за ваше сообщение! В настоящее время мы работаем над функционалом бота. "
        "Попробуйте использовать команду /start для начала работы."
    )

# Маршрут для вебхуков
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

# Маршрут для установки вебхука
@app.route("/")
def webhook():
    logger.info("Установка вебхука")
    
    # Устанавливаем вебхук
    bot.remove_webhook()
    
    # Получаем URL сервиса из переменной окружения или формируем автоматически
    service_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if service_url:
        webhook_url = f"https://{service_url}/{BOT_TOKEN}"
    else:
        # Если RENDER_EXTERNAL_HOSTNAME не установлена, попробуем использовать имя сервиса
        # Замените 'quantum-compass' на имя вашего сервиса в Render
        webhook_url = f"https://quantum-compass.onrender.com/{BOT_TOKEN}"
    
    logger.info(f"Устанавливаем вебхук: {webhook_url}")
    bot.set_webhook(url=webhook_url)
    
    return "Webhook setup complete", 200

# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    
    # Получаем порт из переменной окружения
    port = int(os.environ.get('PORT', 10000))
    
    # Запускаем Flask на 0.0.0.0
    app.run(host="0.0.0.0", port=port)
