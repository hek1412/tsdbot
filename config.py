import os

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# Поддержка нескольких chat_id через запятую
_chat_id_str = os.environ.get('TELEGRAM_CHAT_ID', '')
TELEGRAM_CHAT_IDS = [cid.strip() for cid in _chat_id_str.split(',') if cid.strip()]

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/data/tasks.db')
SCHEDULER_HOUR = int(os.environ.get('SCHEDULER_HOUR', '9'))
SCHEDULER_MINUTE = int(os.environ.get('SCHEDULER_MINUTE', '0'))
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
