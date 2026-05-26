from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from keyboards.main_menu_inline import get_main_menu_inline
from services.google_sheets import append_test_operation

router = Router()


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
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        text="Главное меню:",
        reply_markup=get_main_menu_inline()
    )


@router.callback_query(F.data == "main:last_operations")
async def handle_last_operations(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.answer(
        "Просмотр последних записей подключим позже.",
        reply_markup=get_main_menu_inline()
    )


@router.callback_query(F.data == "main:check_table")
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
            await callback.message.answer(
                "✅ Тестовая запись добавлена в таблицу.",
                reply_markup=get_main_menu_inline()
            )
        else:
            await callback.message.answer(
                "❌ Скрипт ответил ошибкой.\n\n"
                f"{result}",
                reply_markup=get_main_menu_inline()
            )

    except Exception as error:
        await callback.message.answer(
            "❌ Не получилось добавить тестовую запись.\n\n"
            f"Ошибка: {error}",
            reply_markup=get_main_menu_inline()
        )


@router.callback_query(F.data == "main:admin")
async def handle_admin_menu(callback: CallbackQuery) -> None:
    await callback.answer()

    await callback.message.answer(
        "Админ-меню подключим после базовой записи операций.",
        reply_markup=get_main_menu_inline()
    )


@router.message()
async def handle_unknown_message(message: Message) -> None:
    await message.answer(
        "Пока не понял команду. Выбери действие через меню:",
        reply_markup=get_main_menu_inline()
    )