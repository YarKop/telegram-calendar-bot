import os
import logging
import pytz
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from datetime import datetime
from dotenv import load_dotenv
import speech_recognition as sr
from pydub import AudioSegment
import uuid
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = pytz.timezone('Canada/Eastern')

# Google Calendar
SERVICE_ACCOUNT_INFO = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=credentials)
CALENDAR_ID = 'primary'  # або конкретний ID

# Час активності
START_HOUR = 8
END_HOUR = 24

# Логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def is_active_time():
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

def recognize_voice(file_path: str) -> str:
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_ogg(file_path)
    wav_path = file_path.replace('.oga', '.wav')
    audio.export(wav_path, format='wav')
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language='uk-UA')

def create_event(text: str):
    now = datetime.now(TIMEZONE)
    end = now.replace(minute=now.minute + 30)
    event = {
        'summary': text,
        'start': {'dateTime': now.isoformat(), 'timeZone': 'Canada/Eastern'},
        'end': {'dateTime': end.isoformat(), 'timeZone': 'Canada/Eastern'},
    }
    calendar_service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

def handle_voice(update: Update, context: CallbackContext):
    if not is_active_time():
        update.message.reply_text("⏰ Бот працює з 8:00 до 24:00.")
        return

    voice = update.message.voice
    file_id = voice.file_id
    new_file = context.bot.get_file(file_id)
    filename = f"/tmp/{uuid.uuid4()}.oga"
    new_file.download(filename)

    try:
        text = recognize_voice(filename)
        create_event(text)
        update.message.reply_text(f"✅ Додано подію: {text}")
    except Exception as e:
        logging.error(str(e))
        update.message.reply_text("⚠️ Не вдалося розпізнати повідомлення або додати подію.")

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не встановлено.")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
