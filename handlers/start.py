from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import is_admin
from keyboards.main_menu_inline import get_main_menu_inline
from services.google_sheets import (
    append_test_operation,
    build_user_recent_operations_text,
)

router = Router()


def build_main_menu_text(user_id: int | None = None) -> str:
    text = "Главное меню:"

    if user_id:
        text += f"\n\nТвой Telegram ID: {user_id}"

    return text


def get_user_is_admin(user_id: int | None) -> bool:
    return is_admin(user_id)


async def show_main_menu_for_message(message: Message, show_user_id: bool = False) -> None:
    user = message.from_user
    user_id = user.id if user else None

    await message.answer(
        text=build_main_menu_text(user_id if show_user_id else None),
        reply_markup=get_main_menu_inline(is_admin=get_user_is_admin(user_id)),
    )


async def show_main_menu_for_callback(
    callback: CallbackQuery,
    text: str = "Главное меню:",
) -> None:
    user = callback.from_user
    user_id = user.id if user else None

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_main_menu_inline(is_admin=get_user_is_admin(user_id)),
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=get_main_menu_inline(is_admin=get_user_is_admin(user_id)),
        )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else "друг"

    await message.answer(
        text=(
            f"Привет, {user_name}!\n\n"
            "Я бот для учета доходов и расходов по сезону.\n"
            "Пока я запущен в тестовом режиме.\n\n"
            "Выбери действие:"
        ),
        reply_markup=ReplyKeyboardRemove(),
    )

    await show_main_menu_for_message(message, show_user_id=True)


@router.callback_query(lambda callback: callback.data == "main:last_operations")
async def handle_last_operations(callback: CallbackQuery) -> None:
    await callback.answer()

    user = callback.from_user
    user_id = user.id if user else None

    if user_id is None:
        await show_main_menu_for_callback(
            callback,
            "📄 Мои последние записи\n\n"
            "Не удалось определить пользователя.",
        )
        return

    try:
        text = build_user_recent_operations_text(user_id=user_id, limit=5)

        await show_main_menu_for_callback(
            callback,
            text,
        )

    except Exception as error:
        await show_main_menu_for_callback(
            callback,
            "❌ Не получилось получить последние записи.\n\n"
            f"Ошибка: {error}",
        )


@router.callback_query(lambda callback: callback.data == "main:check_table")
async def handle_check_table(callback: CallbackQuery) -> None:
    await callback.answer()

    user = callback.from_user

    try:
        result = append_test_operation(
            user_id=user.id if user else 0,
            username=user.username if user else "",
            full_name=user.full_name if user else "",
        )

        if result.get("ok"):
            text = "✅ Тестовая запись добавлена в таблицу."
        else:
            text = (
                "❌ Скрипт ответил ошибкой.\n\n"
                f"{result}"
            )

        await show_main_menu_for_callback(
            callback,
            text,
        )

    except Exception as error:
        await show_main_menu_for_callback(
            callback,
            "❌ Не получилось добавить тестовую запись.\n\n"
            f"Ошибка: {error}",
        )


@router.message()
async def handle_unknown_message(message: Message) -> None:
    await message.answer(
        "Пока не понял команду. Выбери действие через меню:",
        reply_markup=get_main_menu_inline(
            is_admin=get_user_is_admin(message.from_user.id if message.from_user else None)
        ),
    )