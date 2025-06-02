import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from pydub import AudioSegment
import speech_recognition as sr
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Завантаження .env змінних
load_dotenv()

# Зберегти credentials.json зі змінної середовища
if not os.path.exists("credentials.json"):
    creds_content = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_content:
        with open("credentials.json", "w") as f:
            f.write(creds_content)
    else:
        raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT_JSON is empty or not set")

# Константи
BOT_TOKEN = os.getenv("BOT_TOKEN")
CALENDAR_ID = os.getenv("CALENDAR_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERVICE_ACCOUNT_FILE = "credentials.json"
TIMEZONE = pytz.timezone("Canada/Eastern")
START_HOUR = 8
END_HOUR = 24

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Час активності бота
def is_active_time() -> bool:
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

# Парсинг події GPT
def parse_event_with_gpt(text):
    current_year = datetime.now().year
    prompt = (
        f"Сьогодні {current_year} рік. "
        "Виділи з тексту дату, час і короткий опис події. "
        "Формат відповіді: YYYY-MM-DD HH:MM | Назва події.\n"
        f"Текст: {text}"
    )
    try:
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

        now = datetime.now()
        if event_time.year < now.year:
            try:
                event_time = event_time.replace(year=now.year)
            except ValueError:
                event_time = now + timedelta(days=1)
                event_time = event_time.replace(hour=event_time.hour, minute=0)

        # Якщо дата в минулому навіть у правильному році — не додавати
        if event_time < now:
            raise ValueError("Дата в минулому")

        event_time = TIMEZONE.localize(event_time)
        return summary, event_time

    except Exception as e:
        logging.error(f"GPT parsing error: {e}")
        return None, None

# Додати подію в календар
def add_event_to_calendar(summary, event_time):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)
        end_time = event_time + timedelta(hours=1)
        event = {
            "summary": summary,
            "start": {"dateTime": event_time.isoformat(), "timeZone": str(TIMEZONE)},
            "end": {"dateTime": end_time.isoformat(), "timeZone": str(TIMEZONE)}
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception as e:
        logging.error(f"Google Calendar error: {e}")
        return False

# Обробник голосових
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_active_time():
        await update.message.reply_text("⏰ Бот працює лише з 8:00 до 24:00. Повідомлення не приймаються в цей час.")
        return

    file = await context.bot.get_file(update.message.voice.file_id)
    file_path = "voice.ogg"
    await file.download_to_drive(file_path)
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
                await update.message.reply_text("❌ Не вдалося зчитати дату або час. Спробуйте перефразувати.")
                return

            success = add_event_to_calendar(summary, event_time)
            if success:
                await update.message.reply_text(f"✅ Подія додана: {summary} о {event_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                await update.message.reply_text("❌ Не вдалося додати подію до календаря.")
        except sr.UnknownValueError:
            await update.message.reply_text("❌ Не вдалося розпізнати голосове повідомлення.")
        except Exception as e:
            logging.error(f"Помилка: {e}")
            await update.message.reply_text("❌ Сталася помилка під час обробки повідомлення.")

# Запуск бота
async def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не встановлено. Перевірте .env або змінні Railway.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
