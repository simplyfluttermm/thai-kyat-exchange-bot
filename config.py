import os

# Telegram Bot Token from @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Initial Admin ID (The user who first sets up the bot)
# You can get your ID from @userinfobot
INITIAL_ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
