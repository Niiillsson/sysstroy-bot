from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from config import is_admin
from keyboards.admin_inline import get_admin_menu_inline
from keyboards.main_menu_inline import get_main_menu_inline
from services.google_sheets import (
    build_all_recent_operations_text,
    build_today_summary_text,
)

router = Router()


def get_user_is_admin(user_id: int | None) -> bool:
    return is_admin(user_id)


async def safe_edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as error:
        error_text = str(error)

        if "message is not modified" in error_text:
            return

        await callback.message.answer(
            text=text,
            reply_markup=reply_markup,
        )


async def show_admin_menu(callback: CallbackQuery, text: str | None = None) -> None:
    await safe_edit_message(
        callback=callback,
        text=text or (
            "⚙️ Админ-меню\n\n"
            "Выбери действие:"
        ),
        reply_markup=get_admin_menu_inline(),
    )


async def show_main_menu(callback: CallbackQuery, text: str = "Главное меню:") -> None:
    user = callback.from_user
    user_id = user.id if user else None

    await safe_edit_message(
        callback=callback,
        text=text,
        reply_markup=get_main_menu_inline(is_admin=get_user_is_admin(user_id)),
    )


@router.callback_query(F.data == "main:admin")
async def handle_admin_menu(callback: CallbackQuery) -> None:
    user = callback.from_user
    user_id = user.id if user else None

    if not get_user_is_admin(user_id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()
    await show_admin_menu(callback)


@router.callback_query(F.data == "admin:back_to_main")
async def handle_admin_back_to_main(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_main_menu(callback)


@router.callback_query(F.data == "admin:last_operations")
async def handle_admin_last_operations(callback: CallbackQuery) -> None:
    user = callback.from_user
    user_id = user.id if user else None

    if not get_user_is_admin(user_id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()

    try:
        text = build_all_recent_operations_text(limit=10)

        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_admin_menu_inline(),
        )

    except Exception as error:
        await safe_edit_message(
            callback=callback,
            text=(
                "❌ Не получилось получить последние операции.\n\n"
                f"Ошибка: {error}"
            ),
            reply_markup=get_admin_menu_inline(),
        )


@router.callback_query(F.data == "admin:today_summary")
async def handle_admin_today_summary(callback: CallbackQuery) -> None:
    user = callback.from_user
    user_id = user.id if user else None

    if not get_user_is_admin(user_id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()

    try:
        text = build_today_summary_text()

        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_admin_menu_inline(),
        )

    except Exception as error:
        await safe_edit_message(
            callback=callback,
            text=(
                "❌ Не получилось собрать сводку за сегодня.\n\n"
                f"Ошибка: {error}"
            ),
            reply_markup=get_admin_menu_inline(),
        )


@router.callback_query(F.data == "admin:users_operations")
async def handle_admin_users_operations(callback: CallbackQuery) -> None:
    user = callback.from_user
    user_id = user.id if user else None

    if not get_user_is_admin(user_id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.answer()

    await safe_edit_message(
        callback=callback,
        text=(
            "👥 Операции по пользователям\n\n"
            "Этот раздел добавим после сводки за сегодня."
        ),
        reply_markup=get_admin_menu_inline(),
    )