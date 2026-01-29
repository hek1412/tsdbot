import os

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/data/tasks.db')
SCHEDULER_HOUR = int(os.environ.get('SCHEDULER_HOUR', '9'))
SCHEDULER_MINUTE = int(os.environ.get('SCHEDULER_MINUTE', '0'))
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
