import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")
GOOGLE_SCRIPT_SECRET = os.getenv("GOOGLE_SCRIPT_SECRET")

if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в .env")

if not SPREADSHEET_ID:
    raise ValueError("Не найден SPREADSHEET_ID в .env")

if not GOOGLE_SCRIPT_URL:
    raise ValueError("Не найден GOOGLE_SCRIPT_URL в .env")

if not GOOGLE_SCRIPT_SECRET:
    raise ValueError("Не найден GOOGLE_SCRIPT_SECRET в .env")