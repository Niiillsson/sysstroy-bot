import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")
GOOGLE_SCRIPT_SECRET = os.getenv("GOOGLE_SCRIPT_SECRET")

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")


def parse_admin_ids(raw_value: str) -> set[int]:
    admin_ids: set[int] = set()

    for item in raw_value.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            admin_ids.add(int(item))
        except ValueError:
            raise ValueError(
                "Некорректное значение ADMIN_IDS в .env. "
                "Используй формат: ADMIN_IDS=123456789,987654321"
            )

    return admin_ids


ADMIN_IDS = parse_admin_ids(ADMIN_IDS_RAW)


def is_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False

    return user_id in ADMIN_IDS


if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в .env")

if not SPREADSHEET_ID:
    raise ValueError("Не найден SPREADSHEET_ID в .env")

if not GOOGLE_SCRIPT_URL:
    raise ValueError("Не найден GOOGLE_SCRIPT_URL в .env")

if not GOOGLE_SCRIPT_SECRET:
    raise ValueError("Не найден GOOGLE_SCRIPT_SECRET в .env")