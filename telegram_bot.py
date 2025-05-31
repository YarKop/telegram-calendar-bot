import os
import logging
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters

# Завантажити токен з .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def handle_voice(update, context):
    update.message.reply_text("🎙️ Дякую, отримав голосове повідомлення!")

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не знайдено. Перевір .env або змінні середовища.")
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
