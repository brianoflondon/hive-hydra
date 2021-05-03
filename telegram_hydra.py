from telegram.ext import Updater
import os
import logging


t_key = os.getenv('TELEGRAM_BOT_KEY')
updater = Updater(token=t_key, use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

# def start(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

# from telegram.ext import CommandHandler
# start_handler = CommandHandler('start', start)
# dispatcher.add_handler(start_handler)

# updater.start_polling()

import telegram

# find chat_id : https://t.me/username_to_id_bot
bot = telegram.Bot(token=t_key)
bot.send_message(chat_id="-1001375564114",text="Hello World")
