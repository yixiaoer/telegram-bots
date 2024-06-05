# Hydration Reminder Bot

Hydration Reminder Bot is a Telegram bot designed to help you stay hydrated by reminding you to **drink water** throughout the day. It can also be configured to remind you of other tasks, such as **taking medicine**.

## Usage

```sh
python3.12 -m venv venv
. venv/bin/python
pip install -r requirements.txt
```

Run:

```sh
python main.py
```

Then interact with the bot on Telegram, here's a quick guide:

- **Reset Daily**: Tap "Today" to reset your daily water intake reminder.

- **View Settings**: Tap "View Settings" to see:
    - Current end time
    - Current special note (if any)
    - Today's water intake
    - Next reminder time and message

- **Record water intake**: Tap "+1" to record each cup of water you drink.

- **Set End Time**: Send a message with a number between 0 and 23 to set your desired end time (e.g., "23" sets end time to 11:00 PM).

- **Add Special Notes**: Send a text message with an integer between 1 and 8 followed by your note (e.g., "2 Time for exercise!", then this note will be included in the second cup of water reminder).
