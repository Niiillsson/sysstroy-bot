from datetime import datetime
from uuid import uuid4

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from services.google_sheets import append_operation
from keyboards.main_menu_inline import get_main_menu_inline
from keyboards.operation_inline import build_inline_keyboard


router = Router()


class OperationStates(StatesGroup):
    operation_type = State()
    operation_date = State()
    location = State()
    payer = State()
    payer_manual = State()
    amount = State()
    is_cash = State()
    category = State()
    group = State()
    comment = State()
    confirm = State()


LOCATIONS = [
    {"id": "loc_001", "name": "Пахра"},
    {"id": "loc_002", "name": "Беседка"},
    {"id": "loc_003", "name": "Борисовские пруды"},
    {"id": "loc_004", "name": "Царицыно"},
    {"id": "loc_005", "name": "Булатниково"},
]


CATEGORIES = {
    "expense": [
        {"id": "cat_exp_001", "name": "Продукты"},
        {"id": "cat_exp_002", "name": "Хоз расходы"},
        {"id": "cat_exp_003", "name": "ЗП сотрудников"},
        {"id": "cat_exp_004", "name": "Инвентарь"},
        {"id": "cat_exp_005", "name": "Операционка"},
    ],
    "income": [
        {"id": "cat_inc_001", "name": "Оплата услуги"},
        {"id": "cat_inc_002", "name": "Аренда беседки"},
        {"id": "cat_inc_003", "name": "Мероприятие"},
    ],
}


GROUPS = {
    "cat_exp_001": [
        {"id": "grp_exp_001_001", "name": "Еда на спот"},
        {"id": "grp_exp_001_002", "name": "Напитки"},
        {"id": "grp_exp_001_003", "name": "Сендвичи"},
    ],
    "cat_exp_002": [
        {"id": "grp_exp_002_001", "name": "Расходники"},
        {"id": "grp_exp_002_002", "name": "Уборка"},
    ],
    "cat_exp_003": [
        {"id": "grp_exp_003_001", "name": "Инструкторы"},
        {"id": "grp_exp_003_002", "name": "Администраторы"},
        {"id": "grp_exp_003_003", "name": "Управляющие"},
    ],
    "cat_exp_004": [
        {"id": "grp_exp_004_001", "name": "SUP-оборудование"},
        {"id": "grp_exp_004_002", "name": "Жилеты"},
        {"id": "grp_exp_004_003", "name": "Мелкий инвентарь"},
    ],
    "cat_exp_005": [
        {"id": "grp_exp_005_001", "name": "Сервисы"},
        {"id": "grp_exp_005_002", "name": "Реклама"},
        {"id": "grp_exp_005_003", "name": "Типография"},
    ],
    "cat_inc_001": [
        {"id": "grp_inc_001_001", "name": "Сплав"},
        {"id": "grp_inc_001_002", "name": "SUP-прогулка"},
    ],
    "cat_inc_002": [
        {"id": "grp_inc_002_001", "name": "Беседка"},
    ],
    "cat_inc_003": [
        {"id": "grp_inc_003_001", "name": "Иван Купала"},
        {"id": "grp_inc_003_002", "name": "Песья Пати"},
        {"id": "grp_inc_003_003", "name": "Другое мероприятие"},
    ],
}


PAYERS = {
    "expense": [
        ("-", "minus"),
        ("Антон", "anton"),
        ("Ввести вручную", "manual"),
    ],
    "income": [
        ("Гость / Клиент", "guest_client"),
        ("Заказчик", "customer"),
        ("Ввести вручную", "manual"),
    ],
}


def find_by_id(items: list[dict], item_id: str) -> dict | None:
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def get_operation_type_name(operation_type: str | None) -> str:
    if operation_type == "income":
        return "Доход"
    if operation_type == "expense":
        return "Расход"
    return "Не выбран"


def get_payer_label(operation_type: str | None) -> str:
    if operation_type == "income":
        return "Источник дохода"
    return "Кто платил"


def get_cash_label(value: str | None) -> str:
    return value if value else "Не указано"


def format_amount(amount: int | None) -> str:
    if amount is None:
        return "Не указана"
    return f"{amount:,}".replace(",", " ") + " ₽"


def parse_amount(raw_text: str | None) -> int | None:
    if not raw_text:
        return None

    cleaned = (
        raw_text.strip()
        .replace(" ", "")
        .replace("₽", "")
        .replace("р", "")
        .replace("Р", "")
        .replace(".", "")
    )

    if not cleaned.isdigit():
        return None

    amount = int(cleaned)

    if amount <= 0:
        return None

    return amount


def get_operation_summary(data: dict) -> str:
    operation_type = data.get("operation_type")
    payer_label = get_payer_label(operation_type)

    return (
        "🧾 Добавление операции\n\n"
        f"Тип: {get_operation_type_name(operation_type)}\n"
        f"Дата: {data.get('operation_date', 'Не указана')}\n"
        f"Локация: {data.get('location_name', 'Не выбрана')}\n"
        f"{payer_label}: {data.get('payer', 'Не указан')}\n"
        f"Сумма: {format_amount(data.get('amount'))}\n"
        f"Наличка: {get_cash_label(data.get('is_cash'))}\n"
        f"Категория: {data.get('category_name', 'Не выбрана')}\n"
        f"Группа: {data.get('group_name', 'Не выбрана')}\n"
        f"Комментарий: {data.get('comment') or 'Не указан'}"
    )


async def safe_delete_user_message(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def update_operation_message(
    source: Message | CallbackQuery,
    state: FSMContext,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    data = await state.get_data()

    if isinstance(source, CallbackQuery):
        bot: Bot = source.bot
        chat_id = source.message.chat.id
        current_message_id = source.message.message_id
    else:
        bot: Bot = source.bot
        chat_id = source.chat.id
        current_message_id = data.get("main_message_id")

    main_message_id = data.get("main_message_id") or current_message_id

    if main_message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text=text,
                reply_markup=reply_markup,
            )
            await state.update_data(main_message_id=main_message_id)
            return
        except TelegramBadRequest as error:
            error_text = str(error)

            if "message is not modified" in error_text:
                return

            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            )
            await state.update_data(main_message_id=sent_message.message_id)
            return

    sent_message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )
    await state.update_data(main_message_id=sent_message.message_id)


async def show_operation_type(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(OperationStates.operation_type)

    text = (
        "🧾 Добавление операции\n\n"
        "Выбери тип операции:"
    )

    keyboard = build_inline_keyboard(
        [
            ("Доход", "op_type:income"),
            ("Расход", "op_type:expense"),
        ],
        add_back=False,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


async def show_operation_date(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
    error_text: str | None = None,
) -> None:
    await state.set_state(OperationStates.operation_date)

    data = await state.get_data()

    text = (
        f"{get_operation_summary(data)}\n\n"
        "📅 Укажи дату операции.\n\n"
        "Можно написать дату в формате ДД.ММ.ГГГГ или нажать “Сегодня”."
    )

    if error_text:
        text += f"\n\n⚠️ {error_text}"

    keyboard = build_inline_keyboard(
        [("Сегодня", "op_date:today")],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


async def show_location(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(OperationStates.location)

    data = await state.get_data()

    buttons = [
        (location["name"], f"op_location:{location['id']}")
        for location in LOCATIONS
    ]

    text = (
        f"{get_operation_summary(data)}\n\n"
        "📍 Выбери локацию:"
    )

    await update_operation_message(
        message_or_callback,
        state,
        text,
        build_inline_keyboard(buttons),
    )


async def show_payer(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    operation_type = data["operation_type"]

    await state.set_state(OperationStates.payer)

    if operation_type == "income":
        question = "💰 От кого поступили деньги?"
    else:
        question = "👤 Кто платил?"

    buttons = [
        (label, f"op_payer:{value}")
        for label, value in PAYERS[operation_type]
    ]

    text = (
        f"{get_operation_summary(data)}\n\n"
        f"{question}"
    )

    await update_operation_message(
        message_or_callback,
        state,
        text,
        build_inline_keyboard(buttons),
    )


async def show_payer_manual(
    callback: CallbackQuery,
    state: FSMContext,
    error_text: str | None = None,
) -> None:
    data = await state.get_data()
    operation_type = data["operation_type"]

    await state.set_state(OperationStates.payer_manual)

    if operation_type == "income":
        question = "Напиши, от кого поступили деньги, текстом."
    else:
        question = "Напиши, кто платил, текстом."

    text = (
        f"{get_operation_summary(data)}\n\n"
        f"✍️ {question}"
    )

    if error_text:
        text += f"\n\n⚠️ {error_text}"

    keyboard = build_inline_keyboard(
        [],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(callback, state, text, keyboard)


async def show_amount(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
    error_text: str | None = None,
) -> None:
    await state.set_state(OperationStates.amount)

    data = await state.get_data()

    text = (
        f"{get_operation_summary(data)}\n\n"
        "💵 Укажи сумму сообщением.\n\n"
        "Например: 3500 или 3 500"
    )

    if error_text:
        text += f"\n\n⚠️ {error_text}"

    keyboard = build_inline_keyboard(
        [],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


async def show_is_cash(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(OperationStates.is_cash)

    data = await state.get_data()

    text = (
        f"{get_operation_summary(data)}\n\n"
        "💸 Это наличка?"
    )

    keyboard = build_inline_keyboard(
        [
            ("Да", "op_cash:yes"),
            ("Нет", "op_cash:no"),
        ],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


async def show_category(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    operation_type = data["operation_type"]

    await state.set_state(OperationStates.category)

    categories = CATEGORIES[operation_type]
    buttons = [
        (category["name"], f"op_category:{category['id']}")
        for category in categories
    ]

    text = (
        f"{get_operation_summary(data)}\n\n"
        "🏷️ Выбери категорию:"
    )

    await update_operation_message(
        message_or_callback,
        state,
        text,
        build_inline_keyboard(buttons),
    )


async def show_group(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    category_id = data["category_id"]

    await state.set_state(OperationStates.group)

    groups = GROUPS.get(category_id, [])

    if not groups:
        text = (
            f"{get_operation_summary(data)}\n\n"
            "⚠️ Для этой категории пока нет групп."
        )
        await update_operation_message(
            message_or_callback,
            state,
            text,
            build_inline_keyboard([], add_back=True, add_cancel=True),
        )
        return

    buttons = [
        (group["name"], f"op_group:{group['id']}")
        for group in groups
    ]

    text = (
        f"{get_operation_summary(data)}\n\n"
        "📂 Выбери группу:"
    )

    await update_operation_message(
        message_or_callback,
        state,
        text,
        build_inline_keyboard(buttons),
    )


async def show_comment(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(OperationStates.comment)

    data = await state.get_data()

    text = (
        f"{get_operation_summary(data)}\n\n"
        "💬 Добавь комментарий: что это за доход/расход?"
    )

    keyboard = build_inline_keyboard(
        [("Без комментария", "op_comment:empty")],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


async def show_confirmation(
    message_or_callback: Message | CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()

    await state.set_state(OperationStates.confirm)

    text = (
        "✅ Проверь запись перед сохранением:\n\n"
        f"{get_operation_summary(data)}"
    )

    keyboard = build_inline_keyboard(
        [("✅ Подтвердить", "op_confirm")],
        add_back=True,
        add_cancel=True,
    )

    await update_operation_message(message_or_callback, state, text, keyboard)


@router.message(F.text == "➕ Добавить операцию")
async def start_operation_from_reply_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_operation_type(message, state)


@router.callback_query(F.data == "main:add_operation")
async def start_operation_from_inline_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await state.update_data(main_message_id=callback.message.message_id)
    await show_operation_type(callback, state)


@router.callback_query(F.data == "op_cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    await update_operation_message(
        callback,
        state,
        "Операция отменена. Возвращаю в главное меню.",
        get_main_menu_inline(),
    )


@router.callback_query(OperationStates.operation_type, F.data.startswith("op_type:"))
async def process_operation_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    operation_type = callback.data.split(":")[1]

    await state.update_data(
        operation_type=operation_type,
        operation_date=None,
        location_id=None,
        location_name=None,
        payer=None,
        amount=None,
        is_cash=None,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_operation_date(callback, state)


@router.callback_query(OperationStates.operation_date, F.data == "op_back")
async def back_from_date(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_operation_type(callback, state)


@router.callback_query(OperationStates.operation_date, F.data == "op_date:today")
async def process_today_date(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    operation_date = datetime.now().strftime("%Y-%m-%d")

    await state.update_data(operation_date=operation_date)
    await show_location(callback, state)


@router.message(OperationStates.operation_date)
async def process_manual_date(message: Message, state: FSMContext) -> None:
    raw_date = message.text

    await safe_delete_user_message(message)

    try:
        operation_date = datetime.strptime(raw_date, "%d.%m.%Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        await show_operation_date(
            message,
            state,
            "Дата должна быть в формате ДД.ММ.ГГГГ. Например: 25.05.2026",
        )
        return

    await state.update_data(operation_date=operation_date)
    await show_location(message, state)


@router.callback_query(OperationStates.location, F.data == "op_back")
async def back_from_location(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_operation_date(callback, state)


@router.callback_query(OperationStates.location, F.data.startswith("op_location:"))
async def process_location(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    location_id = callback.data.split(":")[1]
    location = find_by_id(LOCATIONS, location_id)

    if not location:
        await update_operation_message(
            callback,
            state,
            "⚠️ Локация не найдена. Попробуй выбрать ещё раз.",
            build_inline_keyboard([], add_back=True, add_cancel=True),
        )
        return

    await state.update_data(
        location_id=location["id"],
        location_name=location["name"],
        payer=None,
        amount=None,
        is_cash=None,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_payer(callback, state)


@router.callback_query(OperationStates.payer, F.data == "op_back")
async def back_from_payer(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_location(callback, state)


@router.callback_query(OperationStates.payer, F.data.startswith("op_payer:"))
async def process_payer(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    payer_value = callback.data.split(":")[1]

    if payer_value == "manual":
        await show_payer_manual(callback, state)
        return

    payer_map = {
        "minus": "-",
        "anton": "Антон",
        "guest_client": "Гость / Клиент",
        "customer": "Заказчик",
    }

    payer = payer_map.get(payer_value)

    if not payer:
        await update_operation_message(
            callback,
            state,
            "⚠️ Не удалось определить значение. Попробуй выбрать ещё раз.",
            build_inline_keyboard([], add_back=True, add_cancel=True),
        )
        return

    await state.update_data(
        payer=payer,
        amount=None,
        is_cash=None,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_amount(callback, state)


@router.callback_query(OperationStates.payer_manual, F.data == "op_back")
async def back_from_payer_manual(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_payer(callback, state)


@router.message(OperationStates.payer_manual)
async def process_payer_manual(message: Message, state: FSMContext) -> None:
    payer = message.text.strip() if message.text else ""

    await safe_delete_user_message(message)

    if not payer:
        await show_payer_manual(
            message,
            state,
            "Значение не должно быть пустым.",
        )
        return

    await state.update_data(
        payer=payer,
        amount=None,
        is_cash=None,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_amount(message, state)


@router.callback_query(OperationStates.amount, F.data == "op_back")
async def back_from_amount(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_payer(callback, state)


@router.message(OperationStates.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text)

    await safe_delete_user_message(message)

    if amount is None:
        await show_amount(
            message,
            state,
            "Сумма должна быть положительным целым числом. Например: 3500 или 3 500",
        )
        return

    await state.update_data(
        amount=amount,
        is_cash=None,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_is_cash(message, state)


@router.callback_query(OperationStates.is_cash, F.data == "op_back")
async def back_from_is_cash(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_amount(callback, state)


@router.callback_query(OperationStates.is_cash, F.data.startswith("op_cash:"))
async def process_is_cash(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    cash_value = callback.data.split(":")[1]
    is_cash = "Да" if cash_value == "yes" else "Нет"

    await state.update_data(
        is_cash=is_cash,
        category_id=None,
        category_name=None,
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_category(callback, state)


@router.callback_query(OperationStates.category, F.data == "op_back")
async def back_from_category(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_is_cash(callback, state)


@router.callback_query(OperationStates.category, F.data.startswith("op_category:"))
async def process_category(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    category_id = callback.data.split(":")[1]

    data = await state.get_data()
    operation_type = data["operation_type"]

    categories = CATEGORIES[operation_type]
    category = find_by_id(categories, category_id)

    if not category:
        await update_operation_message(
            callback,
            state,
            "⚠️ Категория не найдена. Попробуй выбрать ещё раз.",
            build_inline_keyboard([], add_back=True, add_cancel=True),
        )
        return

    await state.update_data(
        category_id=category["id"],
        category_name=category["name"],
        group_id=None,
        group_name=None,
        comment=None,
    )

    await show_group(callback, state)


@router.callback_query(OperationStates.group, F.data == "op_back")
async def back_from_group(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_category(callback, state)


@router.callback_query(OperationStates.group, F.data.startswith("op_group:"))
async def process_group(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    group_id = callback.data.split(":")[1]

    data = await state.get_data()
    category_id = data["category_id"]

    groups = GROUPS.get(category_id, [])
    group = find_by_id(groups, group_id)

    if not group:
        await update_operation_message(
            callback,
            state,
            "⚠️ Группа не найдена. Попробуй выбрать ещё раз.",
            build_inline_keyboard([], add_back=True, add_cancel=True),
        )
        return

    await state.update_data(
        group_id=group["id"],
        group_name=group["name"],
        comment=None,
    )

    await show_comment(callback, state)


@router.callback_query(OperationStates.comment, F.data == "op_back")
async def back_from_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_group(callback, state)


@router.callback_query(OperationStates.comment, F.data == "op_comment:empty")
async def process_empty_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    await state.update_data(comment="")
    await show_confirmation(callback, state)


@router.message(OperationStates.comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    comment = message.text.strip() if message.text else ""

    await safe_delete_user_message(message)

    await state.update_data(comment=comment)
    await show_confirmation(message, state)


@router.callback_query(OperationStates.confirm, F.data == "op_back")
async def back_from_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_comment(callback, state)


@router.callback_query(OperationStates.confirm, F.data == "op_confirm")
async def process_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    data = await state.get_data()
    user = callback.from_user

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "operation_id": str(uuid4()),
        "operation_type": data["operation_type"],
        "operation_date": data["operation_date"],
        "location_id": data["location_id"],
        "location_name": data["location_name"],
        "payer": data["payer"],
        "amount": data["amount"],
        "is_cash": data["is_cash"],
        "category_id": data["category_id"],
        "category_name": data["category_name"],
        "group_id": data["group_id"],
        "group_name": data["group_name"],
        "comment": data["comment"],
        "created_at": now,
        "created_by_id": user.id if user else "",
        "created_by_username": user.username if user and user.username else "",
        "created_by_name": user.full_name if user else "",
        "status": "active",
    }

    try:
        result = append_operation(payload)

        if result.get("ok"):
            await update_operation_message(
                callback,
                state,
                "✅ Запись добавлена в таблицу.\n\n"
                "Можно добавить новую операцию или вернуться в меню.",
                get_main_menu_inline(),
            )
            await state.clear()
        else:
            await update_operation_message(
                callback,
                state,
                "❌ Скрипт ответил ошибкой.\n\n"
                f"{result}",
                get_main_menu_inline(),
            )
            await state.clear()

    except Exception as error:
        await update_operation_message(
            callback,
            state,
            "❌ Не получилось сохранить запись.\n\n"
            f"Ошибка: {error}",
            get_main_menu_inline(),
        )
        await state.clear()