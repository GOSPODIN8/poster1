import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config

logger = logging.getLogger(__name__)


def start_scheduler(post_func):
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)

    for t in config.POST_TIMES_MSK:
        hour, minute = map(int, t.split(":"))
        scheduler.add_job(
            post_func,
            CronTrigger(hour=hour, minute=minute),
            id=f"post_{t}",
            misfire_grace_time=600,
        )
        logger.info(f"Запланирован пост на {t} МСК")

    scheduler.start()
    return scheduler
