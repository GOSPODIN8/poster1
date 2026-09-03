import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@adrian_trape")
CLUB_BOT_LINK = "https://t.me/clubBXOD_bot"

# Времена постинга по МСК (5 раз в день)
POST_TIMES_MSK = ["16:00"]

TIMEZONE = "Europe/Moscow"

DB_PATH = os.getenv("DB_PATH", "posts.db")

TEXT_MODEL = "gemini-3.6-flash"
IMAGE_MODEL = "gemini-3.1-flash-image"
