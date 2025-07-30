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
