from datetime import datetime
from uuid import uuid4

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

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


def find_by_id(items: list[dict], item_id: str) -> dict | None:
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def get_operation_type_name(operation_type: str) -> str:
    if operation_type == "income":
        return "Доход"
    if operation_type == "expense":
        return "Расход"
    return operation_type


async def show_operation_type(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.operation_type)

    text = "Выбери тип операции:"
    keyboard = build_inline_keyboard(
        [
            ("Доход", "op_type:income"),
            ("Расход", "op_type:expense"),
        ],
        add_back=False,
        add_cancel=True,
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, reply_markup=keyboard)
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


async def show_operation_date(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.operation_date)

    await callback.message.answer(
        "Укажи дату операции.\n\n"
        "Можно написать дату в формате ДД.ММ.ГГГГ или нажать “Сегодня”.",
        reply_markup=build_inline_keyboard(
            [("Сегодня", "op_date:today")],
            add_back=True,
            add_cancel=True,
        )
    )


async def show_location(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.location)

    buttons = [
        (location["name"], f"op_location:{location['id']}")
        for location in LOCATIONS
    ]

    await callback.message.answer(
        "Выбери локацию:",
        reply_markup=build_inline_keyboard(buttons)
    )


async def show_payer(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.payer)

    await callback.message.answer(
        "Кто платил?",
        reply_markup=build_inline_keyboard(
            [
                ("-", "op_payer:minus"),
                ("Антон", "op_payer:anton"),
                ("Ввести вручную", "op_payer:manual"),
            ]
        )
    )


async def show_amount(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.amount)

    text = "Укажи сумму. Только число, без пробелов и символов."

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text)
    else:
        await message_or_callback.answer(text)


async def show_is_cash(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.is_cash)

    await callback.message.answer(
        "Это наличка?",
        reply_markup=build_inline_keyboard(
            [
                ("Да", "op_cash:yes"),
                ("Нет", "op_cash:no"),
            ]
        )
    )


async def show_category(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    operation_type = data["operation_type"]

    await state.set_state(OperationStates.category)

    categories = CATEGORIES[operation_type]
    buttons = [
        (category["name"], f"op_category:{category['id']}")
        for category in categories
    ]

    await callback.message.answer(
        "Выбери категорию:",
        reply_markup=build_inline_keyboard(buttons)
    )


async def show_group(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    category_id = data["category_id"]

    await state.set_state(OperationStates.group)

    groups = GROUPS.get(category_id, [])

    if not groups:
        await callback.message.answer("Для этой категории пока нет групп.")
        return

    buttons = [
        (group["name"], f"op_group:{group['id']}")
        for group in groups
    ]

    await callback.message.answer(
        "Выбери группу:",
        reply_markup=build_inline_keyboard(buttons)
    )


async def show_comment(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OperationStates.comment)

    text = "Добавь комментарий: что это за доход/расход?"
    keyboard = build_inline_keyboard(
        [("Без комментария", "op_comment:empty")]
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, reply_markup=keyboard)
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


async def show_confirmation(message_or_callback: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    confirmation_text = (
        "Проверь запись перед сохранением:\n\n"
        f"Тип: {get_operation_type_name(data['operation_type'])}\n"
        f"Дата: {data['operation_date']}\n"
        f"Локация: {data['location_name']}\n"
        f"Кто платил: {data['payer']}\n"
        f"Сумма: {data['amount']}\n"
        f"Наличка: {data['is_cash']}\n"
        f"Категория: {data['category_name']}\n"
        f"Группа: {data['group_name']}\n"
        f"Комментарий: {data['comment'] or '-'}"
    )

    await state.set_state(OperationStates.confirm)

    keyboard = build_inline_keyboard(
        [("✅ Подтвердить", "op_confirm")],
        add_back=True,
        add_cancel=True,
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(confirmation_text, reply_markup=keyboard)
    else:
        await message_or_callback.answer(confirmation_text, reply_markup=keyboard)


@router.message(F.text == "➕ Добавить операцию")
async def start_operation_from_reply_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_operation_type(message, state)


@router.callback_query(F.data == "main:add_operation")
async def start_operation_from_inline_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await show_operation_type(callback, state)


@router.callback_query(F.data == "op_cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    await callback.message.answer(
        "Операция отменена. Возвращаю в главное меню.",
        reply_markup=get_main_menu_inline()
    )


@router.callback_query(OperationStates.operation_type, F.data.startswith("op_type:"))
async def process_operation_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    operation_type = callback.data.split(":")[1]

    await state.update_data(operation_type=operation_type)
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
    try:
        operation_date = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        await message.answer("Дата должна быть в формате ДД.ММ.ГГГГ. Например: 25.05.2026")
        return

    await state.update_data(operation_date=operation_date)
    await state.set_state(OperationStates.location)

    buttons = [
        (location["name"], f"op_location:{location['id']}")
        for location in LOCATIONS
    ]

    await message.answer(
        "Выбери локацию:",
        reply_markup=build_inline_keyboard(buttons)
    )


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
        await callback.message.answer("Локация не найдена.")
        return

    await state.update_data(
        location_id=location["id"],
        location_name=location["name"]
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
        await state.set_state(OperationStates.payer_manual)
        await callback.message.answer("Напиши, кто платил, текстом.")
        return

    payer = "-" if payer_value == "minus" else "Антон"

    await state.update_data(payer=payer)
    await show_amount(callback, state)


@router.callback_query(OperationStates.payer_manual, F.data == "op_back")
async def back_from_payer_manual(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_payer(callback, state)


@router.message(OperationStates.payer_manual)
async def process_payer_manual(message: Message, state: FSMContext) -> None:
    payer = message.text.strip()

    if not payer:
        await message.answer("Напиши, кто платил, текстом.")
        return

    await state.update_data(payer=payer)
    await show_amount(message, state)


@router.message(OperationStates.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("Сумма должна быть целым числом. Например: 3500")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше нуля.")
        return

    await state.update_data(amount=amount)
    await state.set_state(OperationStates.is_cash)

    await message.answer(
        "Это наличка?",
        reply_markup=build_inline_keyboard(
            [
                ("Да", "op_cash:yes"),
                ("Нет", "op_cash:no"),
            ]
        )
    )


@router.callback_query(OperationStates.is_cash, F.data == "op_back")
async def back_from_is_cash(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await show_amount(callback, state)


@router.callback_query(OperationStates.is_cash, F.data.startswith("op_cash:"))
async def process_is_cash(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    cash_value = callback.data.split(":")[1]
    is_cash = "Да" if cash_value == "yes" else "Нет"

    await state.update_data(is_cash=is_cash)
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
        await callback.message.answer("Категория не найдена.")
        return

    await state.update_data(
        category_id=category["id"],
        category_name=category["name"]
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
        await callback.message.answer("Группа не найдена.")
        return

    await state.update_data(
        group_id=group["id"],
        group_name=group["name"]
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
    comment = "" if message.text == "Без комментария" else message.text

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
            await callback.message.answer(
                "✅ Запись добавлена в таблицу.",
                reply_markup=get_main_menu_inline()
            )
            await state.clear()
        else:
            await callback.message.answer(
                "❌ Скрипт ответил ошибкой.\n\n"
                f"{result}",
                reply_markup=get_main_menu_inline()
            )
            await state.clear()

    except Exception as error:
        await callback.message.answer(
            "❌ Не получилось сохранить запись.\n\n"
            f"Ошибка: {error}",
            reply_markup=get_main_menu_inline()
        )
        await state.clear()