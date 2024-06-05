from datetime import datetime, timedelta
import logging
from typing import TypedDict

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, Job, JobQueue, MessageHandler, filters
from tzlocal import get_localzone

from config import TELEGRAM_BOT_TOKEN

DAILY_WATER_GOAL = 8

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class UserInfo(TypedDict):
    remaining_start_time: None | datetime
    end_time: int
    water_count: int
    special_notes: dict[int, str]
    reminder_job: None | Job

UsersInfo = dict[int, UserInfo]

users_info: UsersInfo = {}
default_end_time: int = 22  # Default end time at 10 PM
default_special_notes: dict[int, str] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user  # User(first_name: str, id: int, is_bot: bool, language_code: str, username: str)
    if user is not None and user.id not in users_info and isinstance(user.id, int):
        users_info[user.id] = {
            'remaining_start_time': None,
            'end_time': default_end_time,
            'water_count': 0,
            'special_notes': default_special_notes.copy(),
            'reminder_job': None,
        }

    if update.message is not None and user is not None:
        await update.message.reply_text(
            f'Hi {user.first_name}, I will remind you to drink water every day.\n'
            f'Press "Today" to start your reminder everyday.\n'
            f'Press "+1" when you drink 1 cup of water.\n'
            f'Press "View Setting" during your today record to see the settings.',
            reply_markup=ReplyKeyboardMarkup([['Today', 'View Settings'], ['+1']], resize_keyboard=True)
        )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is not None and update.effective_chat is not None and update.message is not None:
        user_id = user.id
        now = datetime.now()
        users_info[user_id]['remaining_start_time'] = now
        users_info[user_id]['water_count'] = 0

        await update.message.reply_text(f'Hey {user.first_name}! I\'ll keep reminding you to stay hydrated today!')

        next_reminder = calculate_next_reminder(user_id)
        if next_reminder is not None and isinstance(context.job_queue, JobQueue):
            job = context.job_queue.run_once(send_reminder, next_reminder - now, data={'user_id': user_id}, chat_id=update.effective_chat.id)
            users_info[user_id]['reminder_job'] = job

async def setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is not None and update.message is not None:
        user_id = update.effective_user.id
        user_info = users_info[user_id]
        end_time = user_info['end_time']
        special_notes = user_info['special_notes']
        water_count = user_info['water_count']

        if user_info['reminder_job'] is None:
            await update.message.reply_text('Press "Today" to reset the count for today or "+1" to record your water intake!')
        else:
            next_reminder = user_info['reminder_job'].trigger.run_date.astimezone(get_localzone()).strftime('%Y-%m-%d %H:%M:%S')  # type: ignore
            next_reminder_note = user_info['special_notes'].get(water_count + 1, f'You have drunk {water_count} cups of water today. Time to drink more water!') if water_count <= DAILY_WATER_GOAL - 1 else 'Already enough cups of water.' 
            notes_text = '\n'.join([f'{i}: {note}' for i, note in special_notes.items()]) if len(special_notes.items()) > 0 else 'No special note.'

            await update.message.reply_text(
                f'Current end time: {end_time}.\n'
                f'Current special note:\n{notes_text}\n'
                f'Today you\'ve drunk {water_count} cups of water.\n'
                f'The next reminder time: {next_reminder}\n'
                f'The next reminder note: {next_reminder_note}\n'
                f'Set your end time with a number.\n'
                f'Set your special note with a number (1~{DAILY_WATER_GOAL}) and text.'
            )

def replace_next_reminder(user_id: int, user_info: UserInfo, context: ContextTypes.DEFAULT_TYPE) -> None:
    next_reminder = calculate_next_reminder(user_id)
    if next_reminder is not None and isinstance(context.job_queue, JobQueue):
        if user_info['reminder_job'] is not None and not user_info['reminder_job'].removed:
                # the previous one job is not completed, but here to replace to another job, so `schedule_removal`
                user_info['reminder_job'].schedule_removal()

        job = context.job_queue.run_once(send_reminder, next_reminder - datetime.now(), data={'user_id': user_id}, chat_id=user_id)
        user_info['reminder_job'] = job

async def process_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is not None and update.message is not None:
        user_id = update.effective_user.id
        text = update.message.text
        user_info = users_info[user_id]

        if text is not None:
            if text.isdigit():
                end_time = int(text)
                user_info['end_time'] = end_time
                replace_next_reminder(user_id, user_info, context)
                await update.message.reply_text(f'End time has been set to {end_time}:00.')
            else:
                try:
                    parts = text.split(maxsplit=1)
                    cup_number = int(parts[0])
                    note = parts[1]
                    if 1 <= cup_number <= DAILY_WATER_GOAL:
                        user_info['special_notes'][cup_number] = note
                        await update.message.reply_text(f'Special note for cup {cup_number} has been set to: {note}')
                    else:
                        await update.message.reply_text(f'Cup number must be between 1 and {DAILY_WATER_GOAL}.')
                except (IndexError, ValueError):
                    await update.message.reply_text(f'Invalid format. Please enter a number for the end time or a number (1-{DAILY_WATER_GOAL}) followed by a note.')

async def add_one(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is not None and update.message is not None and update.effective_chat is not None:
        user_id = update.effective_user.id
        user_info = users_info[user_id]
        user_info['water_count'] += 1
        user_info['remaining_start_time'] = datetime.now()  # when drink 1 cup of coffee, the start time of the remaining period is `now()`

        await update.message.reply_text(f'This is your {user_info['water_count']} cup of water today.')

        replace_next_reminder(user_id, user_info, context)

def calculate_next_reminder(user_id: int) -> None | datetime:
    user_info = users_info[user_id]
    start_time = user_info['remaining_start_time']
    remaining_cups = DAILY_WATER_GOAL - user_info['water_count']

    if start_time is None or remaining_cups <= 0:
        return None

    end_time_today = start_time.replace(hour=user_info['end_time'], minute=0, second=0, microsecond=0)

    if end_time_today < start_time:
        return None

    remaining_time = (end_time_today - start_time).total_seconds()
    interval = remaining_time / remaining_cups
    next_reminder = start_time + timedelta(seconds=interval)
    return next_reminder

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_ = context.job
    if job_ is not None and job_.chat_id is not None:
        user_id = job_.data['user_id']  # type: ignore
        user_info = users_info[user_id]

        if user_info['water_count'] >= DAILY_WATER_GOAL:
            reminder_text = f"You have drunk {user_info['water_count']} cups of water today. Already enough cups of water."

        next_cup = user_info['water_count'] + 1
        reminder_text = f"You have drunk {user_info['water_count']} cups of water today. Time to drink more water!"
        if next_cup in user_info['special_notes']:
            reminder_text += f'\n{user_info['special_notes'][next_cup]}'

        await context.bot.send_message(job_.chat_id, text=reminder_text)

        now = datetime.now()
        user_info['remaining_start_time'] = now  # when remind 1 time, the start time of the remaining period is `now()`
        next_reminder = calculate_next_reminder(user_id)
        if next_reminder is not None and isinstance(context.job_queue, JobQueue):

            # no need, since the job is already complete
            # if user_info['reminder_job'] is not None and not user_info['reminder_job'].removed:
            #         user_info['reminder_job'].schedule_removal()

            job = context.job_queue.run_once(send_reminder, next_reminder - now, data={'user_id': user_id}, chat_id=user_id)
            user_info['reminder_job'] = job

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Regex('^(Today)$'), today))
    application.add_handler(MessageHandler(filters.Regex('^(View Settings)$'), setting))
    application.add_handler(MessageHandler(filters.Regex(r'^\+1$'), add_one))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_setting))

    application.run_polling()

if __name__ == '__main__':
    main()
