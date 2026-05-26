from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить операцию",
                    callback_data="main:add_operation"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Мои последние записи",
                    callback_data="main:last_operations"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Проверить таблицу",
                    callback_data="main:check_table"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-меню",
                    callback_data="main:admin"
                )
            ],
        ]
    )