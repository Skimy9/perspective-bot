# handlers/nagual_journey.py
# ... остальные импорты ...
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils.nagual_journey import (
    get_journey_state, can_continue_journey, process_answer, STAGES
)
from keyboards.tests_menu import _add_main_menu_button
from database import SessionLocal
import datetime
import os
from utils.analytics import log_event

logger = logging.getLogger(__name__)

# Путь к папке с изображениями
IMAGE_PATH = os.path.join("assets", "images", "path_to_hidden")

# Убедимся, что путь существует при запуске
if not os.path.exists(IMAGE_PATH):
    logger.warning(f"Папка с изображениями не найдена: {IMAGE_PATH}")
    # Попробуем альтернативный путь
    IMAGE_PATH = os.path.join(os.getcwd(), "assets", "images", "path_to_hidden")
    if not os.path.exists(IMAGE_PATH):
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: не найдена папка с изображениями: {IMAGE_PATH}")

# Состояния игры
STATE_JOURNEY_STARTED = "nagual:started"
STATE_JOURNEY_STAGE = "nagual:stage_"
STATE_JOURNEY_COMPLETED = "nagual:completed"

async def start_nagual_journey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало пути к Скрытому"""
    keyboard = [
        [InlineKeyboardButton("Да, я принимаю вызов", callback_data="nagual:start")],
        [InlineKeyboardButton("Нет, я не готов", callback_data="to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    intro = (
        "🌌 <b>ЭТО НЕ ИГРА</b>\n\n"
        "Вы получили это сообщение не случайно. Кто-то — или что-то — выбрало вас.\n\n"
        "<b>Прежде чем продолжить, знайте:</b>\n"
        "• После первого шага вы больше не сможете видеть мир как раньше\n"
        "• Каждая ошибка отбросит вас к началу пути\n"
        "• Нет кнопки \"Назад\" — только путь вперед или небытие\n"
        "• Если вы не готовы потерять себя — закройте это сообщение сейчас\n\n"
        "Вы когда-нибудь замечали, как <i>дрожит</i> реальность в полдень? Как на мгновение пространство становится <i>липким</i>? Это — трещины. Их видят только избранные.\n\n"
        "Что-то ждет вас <b>среди трещин</b>. Оно не придет к вам. Вы должны найти его.\n\n"
        "<b>ВАЖНО:</b> На каждом этапе вам предложат 5 действий. Только одно из них истинно. Остальные — ловушки вашего разума. Выберите мудро.\n\n"
        "<b>Вы готовы увидеть, что скрыто за завесой?</b>"
    )
    
    # Отправляем изображение с текстом как caption
    try:
        image_path = os.path.join(IMAGE_PATH, "intro.png")
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=intro,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            # Залогируем начало пути
            log_event(
                update.effective_user.id, 
                update.effective_user.username or "unknown", 
                "path_started"
            )
        else:
            # Если изображения нет — отправляем только текст
            logger.warning(f"Файл не найден: {image_path}")
            await update.callback_query.edit_message_text(
                text=intro,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            # Залогируем начало пути
            log_event(
                update.effective_user.id, 
                update.effective_user.username or "unknown", 
                "path_started"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки intro.png: {e}")
        try:
            # Пытаемся отредактировать как caption
            await update.callback_query.edit_message_caption(
                caption=intro,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            # Залогируем начало пути
            log_event(
                update.effective_user.id, 
                update.effective_user.username or "unknown", 
                "path_started"
            )
        except Exception as caption_error:
            logger.error(f"Ошибка редактирования caption: {caption_error}")
            try:
                # Если caption тоже не работает, пробуем как текст
                await update.callback_query.edit_message_text(
                    text=intro,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                # Залогируем начало пути
                log_event(
                    update.effective_user.id, 
                    update.effective_user.username or "unknown", 
                    "path_started"
                )
            except Exception as text_error:
                logger.error(f"Ошибка редактирования текста: {text_error}")
                # Если ничего не работает — отправляем новое сообщение
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=intro,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                # Залогируем начало пути
                log_event(
                    update.effective_user.id, 
                    update.effective_user.username or "unknown", 
                    "path_started"
                )


async def handle_nagual_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий на пути к Скрытому"""
    query = update.callback_query
    await query.answer()
    
    # Разбиваем callback_data на части
    parts = query.data.split(":")
    
    if query.data == "nagual:start":
        # Начинаем путь
        context.user_data['nagual_state'] = {
            'current_stage': 0,
            'journey_started': True,
            'completed': False,
            'stage_started': datetime.datetime.now().isoformat()
        }
        await show_stage(update, context, 0)
    
    elif len(parts) >= 4 and parts[0] == "nagual" and parts[1] == "stage":
        stage = int(parts[2])
        answer = int(parts[3])
        
        # Обрабатываем ответ
        with SessionLocal() as session:
            result = process_answer(update.effective_user.id, stage, answer, session)
        
        # Сохраняем состояние
        if 'nagual_state' not in context.user_data:
            context.user_data['nagual_state'] = {}
            
        context.user_data['nagual_state']['current_stage'] = result['next_stage']
        context.user_data['nagual_state']['completed'] = result['completed']
        
        if result['is_correct']:
            if result['completed']:
                # Завершение пути
                completion_message = (
                    "🌌 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
                    "Вы прошли путь. Вы больше не можете видеть мир как раньше. Это не игра. Это новое восприятие.\n\n"
                    "<b>Ваши глаза теперь видят трещины. Ваше сердце чувствует вибрацию реальности. Вы — не тот, кем были вчера.</b>\n\n"
                    "Этот путь не имеет конца. Каждый день вы будете находить новые трещины. Каждый день вы будете выбирать: войти или остаться в старом мире.\n\n"
                    "Но помните: <i>\"Тот, кто видит трещины, сам становится трещиной в иллюзии.\"</i>\n\n"
                    "<b>Вы прошли испытание. Теперь вы — часть пути.</b>"
                )
                
                # Убраны кнопки "Поделиться опытом" и "Напомнить"
                keyboard = [
                    [InlineKeyboardButton("🔄 Начать заново", callback_data="nagual:start")]
                ]
                reply_markup = InlineKeyboardMarkup(_add_main_menu_button(keyboard))
                
                try:
                    image_path = os.path.join(IMAGE_PATH, "final.png")
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as photo:
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=photo,
                                caption=completion_message,
                                reply_markup=reply_markup,
                                parse_mode="HTML"
                            )
                    else:
                        logger.warning(f"Файл не найден: {image_path}")
                        await query.edit_message_caption(
                            caption=completion_message,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки final.png: {e}")
                    await query.edit_message_caption(
                        caption=completion_message,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
            else:
                # Правильный ответ - немедленный переход к следующему этапу
                await show_stage(update, context, result['next_stage'])
        else:
            # ❌ НЕПРАВИЛЬНЫЙ ОТВЕТ
            # ДОБАВЛЕНА КНОПКА "ПРОЙТИ ЗАНОВО"
            keyboard = [
                [InlineKeyboardButton("🔄 Пройти заново", callback_data="nagual:start")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_caption(
                caption=result['message'],
                reply_markup=reply_markup,
                parse_mode="HTML"
            )


async def show_stage(update: Update, context: ContextTypes.DEFAULT_TYPE, stage_num: int):
    """Показывает текущий этап пути"""
    if stage_num >= len(STAGES):
        return
    
    stage = STAGES[stage_num]
    
    # Формируем текст этапа
    text = f"🌌 <b>{stage['title']}</b>\n\n{stage['description']}\n\n<b>Ваши действия:</b>"
    
    # Создаем клавиатуру с вариантами
    buttons = []
    for i, option in enumerate(stage['options']):
        buttons.append([InlineKeyboardButton(f"{i+1}. {option}", 
                                           callback_data=f"nagual:stage:{stage_num}:{i}")])
    
    # Обновляем время начала этапа
    if 'nagual_state' not in context.user_data:
        context.user_data['nagual_state'] = {}
    context.user_data['nagual_state']['stage_started'] = datetime.datetime.now().isoformat()
    
    reply_markup = InlineKeyboardMarkup(_add_main_menu_button(buttons))
    
    # Отправляем изображение с текстом как caption
    try:
        image_path = os.path.join(IMAGE_PATH, f"{stage_num + 1}.png")
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            logger.warning(f"Файл не найден: {image_path}")
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки изображения для этапа {stage_num + 1}: {e}")
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    # Логируем просмотр этапа
    log_event(
        update.effective_user.id, 
        update.effective_user.username or "unknown", 
        "path_stage_viewed", 
        f"stage_{stage_num + 1}"
    )
