import os
import logging
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import speech_recognition as sr
import requests
import json

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = pytz.timezone('Canada/Eastern')

# Увімкнення логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Обмеження активності
START_HOUR = 8
END_HOUR = 24

def is_active_time() -> bool:
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

import re

def parse_time_from_text(text):
    try:
        match = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', text)
        if match:
            hour, minute = map(int, match.groups())
            now = datetime.now(TIMEZONE)
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except Exception as e:
        logging.error(f"Помилка парсингу часу: {e}")
    return None

def add_to_google_calendar(event_summary: str, hour: int, minute: int):
    now = datetime.now(TIMEZONE)
    start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=30)

    event = {
        "summary": event_summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "America/Toronto"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "America/Toronto"},
    }

    calendar_id = os.getenv("CALENDAR_ID")
    access_token = os.getenv("GOOGLE_ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
        headers=headers,
        data=json.dumps(event)
    )

    return response.status_code == 200 or response.status_code == 201

def handle_voice(update: Update, context: CallbackContext):
    if not is_active_time():
        update.message.reply_text("⏰ Бот працює лише з 8:00 до 24:00. Повідомлення не приймаються в цей час.")
        return

    file = update.message.voice.get_file()
    file.download("voice.ogg")

    os.system("ffmpeg -i voice.ogg voice.wav -y")
    recognizer = sr.Recognizer()
    with sr.AudioFile("voice.wav") as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="uk-UA")
        logging.info(f"Розпізнано текст: {text}")

        time_info = parse_time_from_text(text)
        if time_info:
            hour, minute = time_info
            success = add_to_google_calendar(event_summary=text, hour=hour, minute=minute)
            if success:
                update.message.reply_text(f"✅ Подію додано: '{text}' на {hour:02}:{minute:02}")
            else:
                update.message.reply_text("⚠️ Не вдалося додати подію до Google Calendar.")
        else:
            update.message.reply_text("❌ Неможливо зчитати час. Спробуйте сказати в форматі 14:30 або 9:15.")

    except sr.UnknownValueError:
        update.message.reply_text("⚠️ Не вдалося розпізнати повідомлення.")
    except Exception as e:
        logging.error(f"Помилка: {e}")
        update.message.reply_text("⚠️ Сталася помилка під час обробки.")

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не встановлено. Перевірте .env або змінні Railway.")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
