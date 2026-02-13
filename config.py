import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Token
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Database
DATABASE_PATH = "data/bot_database.db"

# Bot Settings
BOT_PREFIX = "!"
BOT_STATUS = "Заявки в клан"
