from datetime import datetime
from uuid import uuid4

import requests

from config import GOOGLE_SCRIPT_URL, GOOGLE_SCRIPT_SECRET


def send_script_request(payload: dict) -> dict:
    payload_with_secret = {
        **payload,
        "secret_token": GOOGLE_SCRIPT_SECRET,
    }

    response = requests.post(
        GOOGLE_SCRIPT_URL,
        json=payload_with_secret,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


def append_operation(payload: dict) -> dict:
    return send_script_request(payload)


def append_test_operation(user_id: int, username: str | None, full_name: str | None) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "operation_id": str(uuid4()),
        "operation_type": "test",
        "operation_date": datetime.now().strftime("%Y-%m-%d"),
        "location_id": "test_location",
        "location_name": "Тестовая локация",
        "payer": "Тест",
        "amount": 1,
        "is_cash": "Нет",
        "category_id": "test_category",
        "category_name": "Тестовая категория",
        "group_id": "test_group",
        "group_name": "Тестовая группа",
        "comment": "Тестовая запись из Telegram-бота",
        "created_at": now,
        "created_by_id": user_id,
        "created_by_username": username or "",
        "created_by_name": full_name or "",
        "status": "active",
    }

    return append_operation(payload)


def normalize_id(value) -> str:
    if value is None:
        return ""

    value_as_string = str(value).strip()

    if value_as_string.endswith(".0"):
        value_as_string = value_as_string[:-2]

    return value_as_string


def normalize_status(value) -> str:
    value_as_string = str(value or "").strip()

    if not value_as_string:
        return "active"

    return value_as_string


def normalize_operation_type(value) -> str:
    return str(value or "").strip()


def parse_amount(value) -> float:
    if value is None:
        return 0

    value_as_string = str(value).strip()

    if not value_as_string:
        return 0

    value_as_string = (
        value_as_string
        .replace("₽", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return float(value_as_string)
    except ValueError:
        return 0


def format_money(value) -> str:
    try:
        amount = int(round(float(value)))
        return f"{amount:,}".replace(",", " ") + " ₽"
    except (TypeError, ValueError):
        return f"{value} ₽"


def extract_date_part(value) -> str:
    if value is None:
        return ""

    value_as_string = str(value).strip()

    if not value_as_string:
        return ""

    # Google Sheets может вернуть дату как:
    # 2026-05-29
    # 2026-05-29 16:43:12
    # 2026-05-29T16:43:12
    return value_as_string[:10]


def is_today_operation(operation: dict) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")

    created_at_date = extract_date_part(operation.get("created_at"))
    operation_date = extract_date_part(operation.get("operation_date"))

    # Для админской сводки главным считаем created_at:
    # то есть операции, которые были добавлены сегодня.
    if created_at_date:
        return created_at_date == today

    # Если created_at почему-то пустой, используем дату операции.
    return operation_date == today


def get_operations() -> list[dict]:
    result = send_script_request(
        {
            "action": "get_operations",
        }
    )

    if not result.get("ok"):
        raise RuntimeError(f"Google Script вернул ошибку: {result}")

    operations = result.get("operations", [])

    if not isinstance(operations, list):
        raise RuntimeError(f"Некорректный формат операций: {result}")

    return operations


def get_user_recent_operations(user_id: int, limit: int = 5) -> list[dict]:
    operations = get_operations()

    user_id_as_string = normalize_id(user_id)

    user_operations = [
        operation
        for operation in operations
        if normalize_id(operation.get("created_by_id")) == user_id_as_string
        and normalize_status(operation.get("status")) == "active"
        and normalize_operation_type(operation.get("operation_type")) != "test"
    ]

    user_operations.sort(
        key=lambda operation: operation.get("created_at", ""),
        reverse=True,
    )

    return user_operations[:limit]


def get_all_recent_operations(limit: int = 10) -> list[dict]:
    operations = get_operations()

    active_operations = [
        operation
        for operation in operations
        if normalize_status(operation.get("status")) == "active"
        and normalize_operation_type(operation.get("operation_type")) != "test"
    ]

    active_operations.sort(
        key=lambda operation: operation.get("created_at", ""),
        reverse=True,
    )

    return active_operations[:limit]


def get_today_operations() -> list[dict]:
    operations = get_operations()

    today_operations = [
        operation
        for operation in operations
        if normalize_status(operation.get("status")) == "active"
        and normalize_operation_type(operation.get("operation_type")) != "test"
        and is_today_operation(operation)
    ]

    today_operations.sort(
        key=lambda operation: operation.get("created_at", ""),
        reverse=True,
    )

    return today_operations


def format_operation_for_message(operation: dict, index: int | None = None) -> str:
    operation_type = normalize_operation_type(operation.get("operation_type"))

    if operation_type == "income":
        operation_type_text = "Доход"
    elif operation_type == "expense":
        operation_type_text = "Расход"
    else:
        operation_type_text = operation_type or "-"

    amount = operation.get("amount", "-")
    operation_date = operation.get("operation_date", "-")
    location_name = operation.get("location_name", "-")
    category_name = operation.get("category_name", "-")
    group_name = operation.get("group_name", "-")
    payer = operation.get("payer", "-")
    comment = operation.get("comment") or "-"

    amount_text = format_money(amount)

    prefix = f"{index}. " if index is not None else ""

    return (
        f"{prefix}{operation_date} · {operation_type_text} · {amount_text}\n"
        f"📍 {location_name}\n"
        f"👤 {payer}\n"
        f"🏷️ {category_name} / {group_name}\n"
        f"💬 {comment}"
    )


def build_debug_operations_text(user_id: int, operations: list[dict]) -> str:
    debug_items = []

    last_operations = operations[-5:]

    for index, operation in enumerate(last_operations, start=1):
        debug_items.append(
            f"{index}. "
            f"type={operation.get('operation_type')}, "
            f"created_by_id={operation.get('created_by_id')}, "
            f"status={operation.get('status')}, "
            f"amount={operation.get('amount')}, "
            f"name={operation.get('created_by_name')}"
        )

    debug_text = "\n".join(debug_items) if debug_items else "Нет строк для диагностики."

    return (
        "📄 Мои последние записи\n\n"
        "По твоему Telegram ID записи не найдены.\n\n"
        f"Твой Telegram ID: {user_id}\n"
        f"Всего операций из таблицы: {len(operations)}\n\n"
        "Последние строки, которые вернула таблица:\n"
        f"{debug_text}"
    )


def build_user_recent_operations_text(user_id: int, limit: int = 5) -> str:
    operations = get_operations()

    if not operations:
        return (
            "📄 Мои последние записи\n\n"
            "Таблица вернула 0 операций."
        )

    user_id_as_string = normalize_id(user_id)

    user_operations = [
        operation
        for operation in operations
        if normalize_id(operation.get("created_by_id")) == user_id_as_string
        and normalize_status(operation.get("status")) == "active"
        and normalize_operation_type(operation.get("operation_type")) != "test"
    ]

    if not user_operations:
        return build_debug_operations_text(user_id=user_id, operations=operations)

    user_operations.sort(
        key=lambda operation: operation.get("created_at", ""),
        reverse=True,
    )

    operations_text = "\n\n".join(
        format_operation_for_message(operation, index)
        for index, operation in enumerate(user_operations[:limit], start=1)
    )

    return (
        "📄 Мои последние записи\n\n"
        f"{operations_text}"
    )


def build_all_recent_operations_text(limit: int = 10) -> str:
    operations = get_all_recent_operations(limit=limit)

    if not operations:
        return (
            "🧾 Последние операции\n\n"
            "Пока нет сохранённых операций."
        )

    operations_text = "\n\n".join(
        format_operation_for_message(operation, index)
        for index, operation in enumerate(operations, start=1)
    )

    return (
        "🧾 Последние операции\n\n"
        f"{operations_text}"
    )


def build_today_summary_text() -> str:
    operations = get_today_operations()

    today = datetime.now().strftime("%Y-%m-%d")

    if not operations:
        return (
            "📊 Сводка за сегодня\n\n"
            f"Дата: {today}\n\n"
            "Сегодня пока нет сохранённых операций."
        )

    income_total = 0
    expense_total = 0
    income_count = 0
    expense_count = 0

    for operation in operations:
        operation_type = normalize_operation_type(operation.get("operation_type"))
        amount = parse_amount(operation.get("amount"))

        if operation_type == "income":
            income_total += amount
            income_count += 1

        elif operation_type == "expense":
            expense_total += amount
            expense_count += 1

    balance = income_total - expense_total
    total_count = income_count + expense_count

    if balance > 0:
        balance_text = f"+{format_money(balance)}"
    elif balance < 0:
        balance_text = f"-{format_money(abs(balance))}"
    else:
        balance_text = format_money(0)

    return (
        "📊 Сводка за сегодня\n\n"
        f"Дата: {today}\n\n"
        f"Доходы: {format_money(income_total)}\n"
        f"Расходы: {format_money(expense_total)}\n"
        f"Итог: {balance_text}\n\n"
        f"Операций всего: {total_count}\n"
        f"Доходов: {income_count}\n"
        f"Расходов: {expense_count}"
    )