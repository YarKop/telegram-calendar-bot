import os
import logging
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

# Налаштування часової зони
TIMEZONE = pytz.timezone('Canada/Eastern')

# Межі активності
START_HOUR = 8
END_HOUR = 24  # не включає 00:00

def is_active_time() -> bool:
    now = datetime.now(TIMEZONE)
    return START_HOUR <= now.hour < END_HOUR

# Обробка голосових повідомлень
def handle_voice(update: Update, context: CallbackContext):
    if is_active_time():
        update.message.reply_text("🎙️ Дякую, отримав голосове повідомлення!")
    else:
        update.message.reply_text("⏰ Бот працює лише з 8:00 до 24:00. Повідомлення не приймаються в цей час.")

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
