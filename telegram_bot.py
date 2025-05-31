import os
import logging
from telegram.ext import Updater, MessageHandler, Filters
from dotenv import load_dotenv

# Завантажити змінні з .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Увімкнути логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def handle_voice(update, context):
    update.message.reply_text("🎙️ Дякую, отримав голосове повідомлення!")

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не встановлено. Перевірте .env або Railway Variables.")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
