from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить операцию")],
            [KeyboardButton(text="📄 Мои последние записи")],
            [KeyboardButton(text="🔗 Проверить таблицу")],
            [KeyboardButton(text="⚙️ Админ-меню")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие"
    )