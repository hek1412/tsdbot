from apscheduler.schedulers.background import BackgroundScheduler
import config
from app.bot import notify_today_tasks
from app.models import TaskDB


def start_scheduler(app):
    db = TaskDB(config.DATABASE_PATH)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        notify_today_tasks,
        'cron',
        hour=config.SCHEDULER_HOUR,
        minute=config.SCHEDULER_MINUTE,
        args=[db],
        id='daily_notification',
        replace_existing=True,
    )
    scheduler.start()
    print(f'[SCHEDULER] Started, daily check at {config.SCHEDULER_HOUR:02d}:{config.SCHEDULER_MINUTE:02d}')
