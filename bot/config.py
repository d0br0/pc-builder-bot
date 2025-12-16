import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY")