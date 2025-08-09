# handlers/tests.py
import logging
import time
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import BadRequest, TimedOut, RetryAfter
from tests.test_factory import TestFactory
from keyboards.tests_menu import (
    _add_main_menu_button,
    get_main_inline_keyboard,
    get_categories_keyboard,
    get_tests_keyboard,
    get_question_keyboard
)
from utils.analytics import log_event  # ← Добавлен импорт для статистики

# Создаём логгер для этого модуля
logger = logging.getLogger(__name__)

# Флаг: включать ли отладочные логи
DEBUG_LOGS = False  # Установите True, если хотите видеть ВСЕ логи

def debug_log(message):
    """Условная отладка — выводит сообщение только если DEBUG_LOGS = True"""
    if DEBUG_LOGS:
        logger.debug(message)


async def safe_edit_message(update: Update, text: str, reply_markup=None, max_retries=3):
    """
    Безопасное редактирование сообщения с определением типа
    """
    for attempt in range(max_retries):
        try:
            # Проверяем, есть ли в сообщении фото
            if update.callback_query.message.photo:
                await update.callback_query.edit_message_caption(
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            return True
        except TimedOut:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info("ℹ️ Сообщение не изменилось — это нормально")
                return True
            logger.error(f"BadRequest при редактировании: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка редактирования: {e}")
            return False
    return False


async def handle_main_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка главного меню"""
    query = update.callback_query
    await query.answer()

    if query.data == "show_categories":
        await show_categories_menu(update)
    elif query.data == "to_main":
        await show_main_menu(update)


async def show_main_menu(update: Update):
    """Показывает главное меню"""
    try:
        # Определяем, есть ли в сообщении фото
        if update.callback_query.message.photo:
            await update.callback_query.edit_message_caption(
                caption="Привет! Выбери действие:",
                reply_markup=get_main_inline_keyboard()
            )
        else:
            await update.callback_query.edit_message_text(
                text="Привет! Выбери действие:",
                reply_markup=get_main_inline_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при показе главного меню: {e}")
        # Fallback: отправляем новое сообщение
        await update.callback_query.message.reply_text(
            "Привет! Выбери действие:",
            reply_markup=get_main_inline_keyboard()
        )


async def show_categories_menu(update: Update):
    """Показывает меню категорий"""
    try:
        await update.callback_query.edit_message_caption(
            caption="Выберите категорию тестов:",
            reply_markup=get_categories_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при показе категорий: {e}")
        try:
            await update.callback_query.edit_message_text(
                text="Выберите категорию тестов:",
                reply_markup=get_categories_keyboard(),
                parse_mode='HTML'
            )
        except:
            await update.callback_query.message.reply_text(
                "Выберите категорию тестов:",
                reply_markup=get_categories_keyboard(),
                parse_mode='HTML'
            )


async def show_tests_menu(update: Update, category_id: str):
    """Показывает тесты в категории"""
    try:
        await update.callback_query.edit_message_caption(
            caption="Выберите тест:",
            reply_markup=get_tests_keyboard(category_id)
        )
    except Exception as e:
        logger.error(f"Ошибка при показе тестов: {e}")
        try:
            await update.callback_query.edit_message_text(
                text="Выберите тест:",
                reply_markup=get_tests_keyboard(category_id),
                parse_mode='HTML'
            )
        except:
            await update.callback_query.message.reply_text(
                "Выберите тест:",
                reply_markup=get_tests_keyboard(category_id),
                parse_mode='HTML'
            )

async def handle_category_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    query = update.callback_query
    await query.answer()

    # КРИТИЧЕСКИ ВАЖНО: сброс состояния Пути к Скрытому
    reset_nagual_state(context)
    
    category_id = query.data.split('_', 1)[1]
    await show_tests_menu(update, category_id)


async def handle_test_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка начала теста"""
    query = update.callback_query
    await query.answer()
    
    # КРИТИЧЕСКИ ВАЖНО: сброс состояния Пути к Скрытому
    reset_nagual_state(context)
    
    if not query.data.startswith("test_"):
        return

    test_id = query.data.split("_", 1)[1]

    # Только если DEBUG_LOGS = True
    debug_log(f"🚀 handle_test_action: запуск теста {test_id}")

    test = TestFactory.get_test(test_id)
    if not test:
        logger.warning(f"❌ Тест не найден: {test_id}")
        await query.edit_message_text("❌ Ошибка: тест не найден.")
        return

    if not hasattr(test, 'questions') or not hasattr(test, 'options'):
        logger.error(f"❌ Тест {test_id} повреждён: нет questions или options")
        await query.edit_message_text("❌ Ошибка: повреждённый тест.")
        return

    # Логируем начало теста
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    log_event(user_id, username, "test_started", test_id)

    context.user_data['current_test'] = {
        'id': test_id,
        'answers': []
    }

    try:
        await show_question(update, context, test, 0)
        debug_log(f"✅ Тест {test_id} запущен")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска теста {test_id}: {e}", exc_info=True)
        await query.edit_message_text("❌ Ошибка загрузки теста.")


async def handle_back_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки Назад"""
    query = update.callback_query
    await query.answer()

    if query.data == "to_categories":
        await show_categories_menu(update)
    elif query.data == "to_main":
        await show_main_menu(update)


async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE, test, question_num: int):
    """Показывает текущий вопрос"""
    try:
        if not 0 <= question_num < len(test.questions):
            raise IndexError(f"Неверный номер вопроса: {question_num}")

        if 'current_test' in context.user_data:
            context.user_data['current_test']['current_question'] = question_num

        question_text = (
            f"📝 <b>{test.name}</b>\n"
            f"❓ Вопрос {question_num + 1}/{len(test.questions)}:\n"
            f"{test.questions[question_num]}"
        )

        reply_markup = get_question_keyboard(test, question_num)

        if not await safe_edit_message(update, question_text, reply_markup):
            await update.callback_query.answer("❌ Не удалось загрузить вопрос.")

    except Exception as e:
        logger.error(f"Ошибка показа вопроса {question_num}: {e}", exc_info=True)
        await update.callback_query.answer("❌ Ошибка загрузки вопроса.")


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на вопрос"""
    query = update.callback_query
    try:
        await query.answer()
        await asyncio.sleep(0.1)

        parts = query.data.split('_')
        if len(parts) != 3:
            debug_log(f"Неверный формат callback_data: {query.data}")
            return

        q_num = int(parts[1])
        a_num = int(parts[2])

        test_data = context.user_data.get('current_test')
        if not test_data:
            await query.edit_message_text("❌ Ошибка: данные теста утеряны.")
            return

        test = TestFactory.get_test(test_data['id'])
        if not test:
            await query.edit_message_text("❌ Ошибка: тест не найден.")
            return

        if q_num >= len(test.questions):
            debug_log(f"❌ Неверный номер вопроса: {q_num}")
            return
        if a_num >= len(test.options[q_num]):
            debug_log(f"❌ Неверный номер ответа: {a_num}")
            return

        # Логируем ответ на вопрос
        user_id = update.effective_user.id
        username = update.effective_user.username or "unknown"
        log_event(user_id, username, "answer_given", f"{test_data['id']}_q{q_num}")

        answers = test_data['answers']
        if len(answers) <= q_num:
            answers.append(a_num)
        else:
            answers[q_num] = a_num

        next_question = q_num + 1
        if next_question < len(test.questions):
            await show_question(update, context, test, next_question)
        else:
            await finish_test(update, context)

    except TimedOut:
        logger.warning("Таймаут при обработке ответа")
        await query.answer("⏳ Задержка, пожалуйста, подождите.")
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}", exc_info=True)
        await query.answer("❌ Ошибка обработки ответа.")


async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение теста"""
    test_data = context.user_data.get('current_test')
    if not test_data:
        logger.warning("❌ Данные теста утеряны при завершении")
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("Произошла ошибка. Попробуйте начать тест заново.")
        return

    test = TestFactory.get_test(test_data['id'])
    if not test:
        logger.warning(f"❌ Тест {test_data['id']} не найден")
        await update.callback_query.edit_message_text("❌ Ошибка: тест не найден.")
        return

    answers = test_data.get('answers', [])
    if len(answers) != len(test.questions):
        logger.warning("❌ Не все вопросы были отвечены")
        await update.callback_query.edit_message_text("❌ Не все вопросы были отвечены.")
        return

    try:
        result = test.interpret(answers)
        text = f"<b>{result['result']}</b>\n\n{result['advice']}"
        reply_markup = InlineKeyboardMarkup(_add_main_menu_button([]))
        
        # Логируем завершение теста
        user_id = update.effective_user.id
        username = update.effective_user.username or "unknown"
        log_event(user_id, username, "test_completed", test_data['id'])
        
        await safe_edit_message(update, text, reply_markup)
    except Exception as e:
        logger.error(f"Ошибка завершения теста: {e}", exc_info=True)
    finally:
        # КРИТИЧЕСКИ ВАЖНО: сброс состояния теста
        if 'current_test' in context.user_data:
            del context.user_data['current_test']

        await update.callback_query.edit_message_text("❌ Произошла ошибка при обработке результатов.")

