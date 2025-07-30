import telebot
from random import choice
import os
from flask import Flask, request

# Получаем токен из переменных окружения
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
        "🔮 *Вы только что сделали первый шаг к изменению своей реальности*\n\n"
        "Здесь вы получите вопросы, которые:\n"
        "✓ Выведут вас за рамки шаблонного мышления\n"
        "✓ Помогут увидеть то, что скрыто от обычного взгляда\n"
        "✓ Создадут новые точки опоры в вашем восприятии\n\n"
        "Нажмите /question, чтобы получить свой первый вопрос.\n\n"
        "_Этот вопрос пришел к вам не случайно. "
        "Он появился именно сейчас, потому что вы готовы к новому взгляду._",
        parse_mode='Markdown')

@bot.message_handler(commands=['question'])
def send_perspective(message):
    question = choice(PERSPECTIVES)
    response = f"🔮 *{question}*\n\n"
    response += "_Этот вопрос пришел к вам не случайно. "
    response += "Он появился именно сейчас, потому что вы готовы к новому взгляду._\n\n"
    response += "Нажмите /question еще раз, если готовы глубже."
    
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['share'])
def share(message):
    bot.reply_to(message,
        "Поделитесь этим ботом с тем, кто готов увидеть больше:\n"
        f"t.me/{bot.get_me().username}\n\n"
        "P.S. Первые 10 человек, отправивших скриншот бота в личку, "
        "получат доступ к закрытому каналу с ежедневными инсайтами")

# Flask приложение для вебхуков
app = Flask(__name__)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    # Устанавливаем вебхук
    bot.remove_webhook()
    bot.set_webhook(url=f"https://perspective-bot.onrender.com/{BOT_TOKEN}")
    return "Webhook setup complete", 200

if __name__ == "__main__":
    # Получаем порт из переменной окружения
    port = int(os.environ.get('PORT', 10000))
    # Запускаем Flask на 0.0.0.0
    app.run(host="0.0.0.0", port=port)
