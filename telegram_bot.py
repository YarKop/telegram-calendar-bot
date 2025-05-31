import os
import logging
import requests
from pydub import AudioSegment
import speech_recognition as sr
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Завантаження змінних середовища
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Увімкнення логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TIMEZONE = pytz.timezone('Canada/Eastern')
START_HOUR = 8
END_HOUR = 24

def is_active_time() -> bool:
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

def handle_voice(update: Update, context: CallbackContext):
    if not is_active_time():
        update.message.reply_text("⏰ Бот працює лише з 8:00 до 24:00.")
        return

    user = update.message.from_user
    voice = update.message.voice
    file = context.bot.get_file(voice.file_id)
    ogg_path = f"voice_{user.id}.ogg"
    wav_path = f"voice_{user.id}.wav"

    file.download(ogg_path)

    try:
        audio = AudioSegment.from_file(ogg_path)
        audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uk-UA")

        update.message.reply_text(f"🗣 Розпізнано: {text}")
        
        # Наступний крок: обробити `text` як подію та додати в календар

    except Exception as e:
        update.message.reply_text(f"⚠️ Помилка розпізнавання: {e}")
    finally:
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)

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
