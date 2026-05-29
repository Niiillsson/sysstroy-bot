from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Сводка за сегодня",
                    callback_data="admin:today_summary",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧾 Последние операции всех",
                    callback_data="admin:last_operations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Операции по пользователям",
                    callback_data="admin:users_operations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="admin:back_to_main",
                )
            ],
        ]
    )