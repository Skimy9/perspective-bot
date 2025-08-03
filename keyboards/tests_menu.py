# tests_menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_feedback_keyboard(user_id=None):
    """Клавиатура для обратной связи"""
    buttons = []
    if user_id:
        buttons.append([InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_to_{user_id}")])
    buttons.append([InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")])
    return InlineKeyboardMarkup(buttons)


def _add_main_menu_button(buttons):
    """Добавляет кнопку возврата в главное меню"""
    if not any("to_main" in btn.callback_data for row in buttons for btn in row):
        buttons.append([InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")])
    return buttons



def get_main_inline_keyboard(is_admin=False):
    buttons = [
        [InlineKeyboardButton("🧠 Пройти тесты", callback_data="show_categories")],
        [InlineKeyboardButton("🌀 Путь к Скрытому", callback_data="nagual_intro")],
        [InlineKeyboardButton("✉️ Написать автору", callback_data="ask_author")]
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        ])
        buttons.append([
            InlineKeyboardButton("📬 Новые сообщения", callback_data="admin_unanswered")
        ])

    return InlineKeyboardMarkup(buttons)


def get_categories_keyboard():
    """Меню категорий"""
    categories = {
        "esoteric": "🔮 Эзотерика",
        "psychology": "🧠 Психология",
        "personality": "🌟 Личность"
    }
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"category_{cat_id}")]
        for cat_id, name in categories.items()
    ]
    return InlineKeyboardMarkup(_add_main_menu_button(buttons))


def get_tests_keyboard(category_id):
    """Меню тестов"""
    tests = {
        "esoteric": {
            "soul_type": "🔮 Тип вашей души",
            "elemental": "🌪️ Ваши стихии",
            "ayurvedic": "🌿 Аюрведическая доша",
            "magic_path": "🌌 Путь магии"
        },
        "psychology": {
            "depression": "📉 Тест на депрессию",
            "anxiety": "🌀 Тест на тревожность",
            "stress": "💢 Тест на стресс"
        },
        "personality": {
            "bigfive": "🌟 Тест личности Big5",
            "mbti": "🔍 Тест личности (MBTI)"
        },
    }
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"test_{test_id}")]
        for test_id, name in tests.get(category_id, {}).items()
    ]
    return InlineKeyboardMarkup(_add_main_menu_button(buttons))


def get_question_keyboard(test, question_num):
    """Клавиатура вопроса (БЕЗ времени в callback_data)"""
    buttons = [
        [InlineKeyboardButton(option, callback_data=f"answer_{question_num}_{i}")]
        for i, option in enumerate(test.options[question_num])
    ]
    return InlineKeyboardMarkup(_add_main_menu_button(buttons))


def get_post_test_keyboard():
    """Клавиатура после теста"""
    buttons = [
        [InlineKeyboardButton("🧠 Пройти другой тест", callback_data="show_categories")],
    ]
    return InlineKeyboardMarkup(_add_main_menu_button(buttons))