from telegram import Update
from telegram.ext import CallbackContext
from database.crud import save_question

async def handle_question(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    question_text = update.message.text
    
    save_question(user_id, question_text)
    await update.message.reply_text("Ваш вопрос сохранён, автор скоро ответит!")