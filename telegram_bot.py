import os
import logging
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import speech_recognition as sr
from pydub import AudioSegment
import requests
import json
import openai  # Додаємо OpenAI

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CALENDAR_ID = os.getenv("CALENDAR_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERVICE_ACCOUNT_FILE = "credentials.json"

# Увімкнення логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TIMEZONE = pytz.timezone('Canada/Eastern')
START_HOUR = 8
END_HOUR = 24

openai.api_key = OPENAI_API_KEY

def is_active_time() -> bool:
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

def parse_event_with_gpt(text):
    prompt = (
        "Виділи з тексту дату, час і короткий опис події. "
        "Формат відповіді: YYYY-MM-DD HH:MM | Назва події.\n"
        f"Текст: {text}"
    )
    try:
        from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)
result = response.choices[0].message.content.strip()

        parts = result.split('|')
        if len(parts) != 2:
            raise ValueError("Неправильний формат GPT-відповіді")

        dt_str, summary = parts[0].strip(), parts[1].strip()
        event_time = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        event_time = TIMEZONE.localize(event_time)
        return summary, event_time
    except Exception as e:
        logging.error(f"GPT parsing error: {e}")
        return None, None

def add_event_to_calendar(summary, event_time):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{CALENDAR_ID}/events"
    headers = {
        "Authorization": f"Bearer {os.getenv('GOOGLE_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    end_time = event_time + timedelta(hours=1)
    event = {
        "summary": summary,
        "start": {"dateTime": event_time.isoformat(), "timeZone": str(TIMEZONE)},
        "end": {"dateTime": end_time.isoformat(), "timeZone": str(TIMEZONE)}
    }
    response = requests.post(url, headers=headers, data=json.dumps(event))
    return response.status_code == 200 or response.status_code == 201

def handle_voice(update: Update, context: CallbackContext):
    if not is_active_time():
        update.message.reply_text("⏰ Бот працює лише з 8:00 до 24:00. Повідомлення не приймаються в цей час.")
        return

    file = context.bot.get_file(update.message.voice.file_id)
    file_path = "voice.ogg"
    file.download(file_path)
    sound = AudioSegment.from_file(file_path)
    wav_path = "voice.wav"
    sound.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="uk-UA")
            logging.info(f"Розпізнано текст: {text}")
            summary, event_time = parse_event_with_gpt(text)
            if not summary or not event_time:
                update.message.reply_text("❌ Не вдалося зчитати дату або час. Спробуйте перефразувати.")
                return
            success = add_event_to_calendar(summary, event_time)
            if success:
                update.message.reply_text(f"✅ Подія додана: {summary} о {event_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                update.message.reply_text("❌ Не вдалося додати подію до календаря.")
        except sr.UnknownValueError:
            update.message.reply_text("❌ Не вдалося розпізнати голосове повідомлення.")
        except Exception as e:
            logging.error(f"Помилка: {e}")
            update.message.reply_text("❌ Сталася помилка під час обробки повідомлення.")

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
