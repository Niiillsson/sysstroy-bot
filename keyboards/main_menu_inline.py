from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_inline(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Добавить операцию",
                callback_data="main:add_operation",
            )
        ],
        [
            InlineKeyboardButton(
                text="📄 Мои последние записи",
                callback_data="main:last_operations",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔗 Проверить таблицу",
                callback_data="main:check_table",
            )
        ],
    ]

    if is_admin:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-меню",
                    callback_data="main:admin",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)