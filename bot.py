import os
import time
import json
import logging
from datetime import datetime

import telebot
from telebot import types

# Импортируем конфигурацию
from config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(Config.BOT_TOKEN)

# Загрузка данных
def load_data(file_path):
    """Загружает JSON-данные из файла"""
    with open(os.path.join(Config.DATA_DIR, file_path), "r", encoding="utf-8") as f:
        return json.load(f)

# Пример загрузки приветственных сообщений
WELCOME_MESSAGES = load_data("system/welcome_messages.json")

@bot.message_handler(commands=['myid'])
def get_my_id(message):
   bot.reply_to(
       message,
       f"Ваш Telegram ID: `{message.chat.id}`\n\n"
       "Скопируйте это число и вставьте в .env файл как ADMIN_ID",
       parse_mode='Markdown'
)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Выбираем случайное приветственное сообщение с учетом веса
    total_weight = sum(item["weight"] for item in WELCOME_MESSAGES["welcome"])
    rand = random.uniform(0, total_weight)
    cumulative_weight = 0
    
    for item in WELCOME_MESSAGES["welcome"]:
        cumulative_weight += item["weight"]
        if rand < cumulative_weight:
            selected = item
            break
    
    # Отправляем приветствие
    bot.reply_to(
        message, 
        f"{selected['text']}\n\n{WELCOME_MESSAGES['consent']}",
        parse_mode='Markdown'
    )
    
    # Добавляем кнопку для начала
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Начать работу")
    markup.add(btn1)
    
    bot.send_message(
        message.chat.id,
        "Готовы начать свое путешествие к осознанности?",
        reply_markup=markup
    )

# Запуск бота
if __name__ == "__main__":
    logger.info("Бот запущен...")
    
    # Создаем директорию для данных пользователей
    if not os.path.exists(Config.USER_DATA_DIR):
        os.makedirs(Config.USER_DATA_DIR)
    
    # Запускаем polling с обработкой ошибок
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            time.sleep(15)
