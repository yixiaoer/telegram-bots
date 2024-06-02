# TLS Slot Bot

TLS Slot Bot is a Python-based automation tool designed to assist with booking appointments for Swiss visa applications in London. The bot periodically refreshes the TLS Contact website to check for available slots and sends a notification via Telegram when an open slot is found.

## Run

Arch Linux:

```sh
yay -S python-selenium
sudo pacman -S geckodriver
```

Download prerequisites:

```sh
python -m venv venv
. venv/bin/python
pip install -r requirements.txt
```

Config:

```sh
cp config.example.py config.py
modify config.py
```

The items in the configuration are as follows:

- **TLS_USERNAME**: The username for your TLS Contact account.
- **TLS_PASSWORD**: The password for your TLS Contact account.
- **VISA_GRP_ID**: The visa application group ID.
- **TELEGRAM_BOT_TOKEN**: The token for your Telegram bot, obtained from BotFather.
- **TELEGRAM_CHAT_ID**: The chat ID where the bot will send notifications.

Run:

```python
python main.py
```

## How It Works

1. **Login to TLS Contact**: The bot uses your TLS username and password to log in to the TLS Contact website.
2. **Check for Available Slots**: It periodically checks for available appointment slots for the given visa group ID.
3. **Send Notification**: If an available slot is found, the bot sends a notification to your specified Telegram chat ID.
