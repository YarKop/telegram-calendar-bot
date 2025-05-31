from telegram.ext import Updater, MessageHandler, Filters
import logging

BOT_TOKEN = "BOT_TOKEN"

# Увімкнути логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def handle_voice(update, context):
    update.message.reply_text("🎙️ Дякую, отримав голосове повідомлення!")

def main():
    updater = Updater("BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
