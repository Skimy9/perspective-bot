import telebot
from random import choice
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = telebot.TeleBot(BOT_TOKEN)

PERSPECTIVES = [
    "Как бы это выглядело, если бы деньги не существовали?",
    "Что здесь скрыто от вашего внимания?",
    "Как эта ситуация выглядит с точки зрения будущего вас?",
    "Какую игру вы играете, не осознавая этого?",
    "Что здесь является иллюзией, которую вы принимаете за реальность?",
    "Как бы решил эту проблему человек, который видит системы?",
    "Какая эмоция управляет этим процессом?",
    "Какие правила вы не осознаете, но подчиняетесь им?",
    "Что здесь является фоном, а что — главным действием?",
    "Как бы выглядела эта ситуация через призку вашего предназначения?"
]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "👋 Я помогаю выйти за рамки шаблонного мышления\n"
        "Нажмите /question, чтобы получить персональный вопрос\n\n"
        "P.S. Этот вопрос — не случайность. Он пришел к вам не просто так.")

@bot.message_handler(commands=['question'])
def send_perspective(message):
    question = choice(PERSPECTIVES)
    bot.reply_to(message, f"🔮 {question}\n\nНажмите /question еще раз, если готовы глубже")

@bot.message_handler(commands=['share'])
def share(message):
    bot.reply_to(message,
        "Поделитесь этим ботом с тем, кто готов увидеть больше:\n"
        f"t.me/{bot.get_me().username}\n\n"
        "P.S. Первые 10 человек, отправивших скриншот бота в личку, "
        "получат доступ к закрытому каналу с ежедневными инсайтами")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)