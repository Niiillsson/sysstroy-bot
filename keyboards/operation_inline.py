from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_inline_keyboard(
    buttons: list[tuple[str, str]],
    add_back: bool = True,
    add_cancel: bool = True,
) -> InlineKeyboardMarkup:
    keyboard = []

    for text, callback_data in buttons:
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data
            )
        ])

    navigation_row = []

    if add_back:
        navigation_row.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="op_back"
            )
        )

    if add_cancel:
        navigation_row.append(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="op_cancel"
            )
        )

    if navigation_row:
        keyboard.append(navigation_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)