import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN", "7434021456:AAEms42Y-MRdYnmDjnoOcf0HhIdk9hkpVDg")
DATABASE_NAME = "molfa_users.db"
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "427018516"))

# Google Sheets
GOOGLE_SHEETS_ENABLED = True
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1dN3_VUb69e3BlXu-hIXNczNcLgvovvdIMh9QpfROSpQ")

# Для credentials - читаємо зі змінної середовища або файлу
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
if GOOGLE_CREDENTIALS_JSON:
    # Зберігаємо credentials у тимчасовий файл
    GOOGLE_CREDENTIALS_FILE = "/tmp/credentials.json"
    with open(GOOGLE_CREDENTIALS_FILE, 'w') as f:
        json.dump(json.loads(GOOGLE_CREDENTIALS_JSON), f)
else:
    GOOGLE_CREDENTIALS_FILE = "credentials.json"