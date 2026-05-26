from datetime import datetime
from uuid import uuid4

import requests

from config import GOOGLE_SCRIPT_URL, GOOGLE_SCRIPT_SECRET


def append_operation(payload: dict) -> dict:
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