from datetime import datetime

import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID, BOT_CHAT_ID

timezone = pytz.timezone('Asia/Singapore')

def get_time() -> str:
    return datetime.now(timezone).strftime('%-m.%-d %H:%M')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Available', 'Maybe', 'Busy']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    if update.message is not None:
        await update.message.reply_text('Please choose:', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    if update.message.chat_id != BOT_CHAT_ID:
        return

    text = update.message.text

    if text is None:
        return

    if text not in ('Available', 'Maybe', 'Busy'):
        title = f'{get_time()}: {text}'
        await context.bot.set_chat_title(chat_id=GROUP_CHAT_ID, title=title)
    else:
        filename = {
            'Available': 'green.jpg',
            'Maybe': 'yellow.jpg',
            'Busy': 'red.jpg',
        }.get(text, None)

        if filename is None:
            return

        with open(filename, 'rb') as f:
            await context.bot.set_chat_photo(chat_id=GROUP_CHAT_ID, photo=f)

async def delete_group_avatar_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None and update.message.chat.id == GROUP_CHAT_ID:
        await context.bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_PHOTO | filters.StatusUpdate.NEW_CHAT_TITLE, delete_group_avatar_update))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
