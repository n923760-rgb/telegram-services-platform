from zoneinfo import ZoneInfo

from arq import cron
from arq.connections import RedisSettings

from app.core.db import sessions
from app.core.settings import config
from app.files.retention import cleanup, cleanup_terminal_files
from app.ops.notifier import Notifier
from app.ops.reports import daily_report, flush_reports
from app.payments.recovery import refunds
from app.payments.stars import expire_invoices
from app.providers.delivery import TelegramDelivery
from app.providers.notifier import TelegramAdminChannel
from app.providers.runtime import storage
from app.providers.stars import TelegramStars
from app.providers.telegram import create_bot
from app.services.registry import registry
from app.workers.runner import deliver_confirmations, deliver_failures, dispatch, execute_job


async def startup(ctx):
    async with sessions.begin() as db:
        await registry.sync(db)
    ctx["bot"] = create_bot()
    ctx["delivery"] = TelegramDelivery(ctx["bot"], storage())
    ctx["notifier"] = Notifier(ctx["redis"], TelegramAdminChannel(ctx["bot"]))
    ctx["stars"] = TelegramStars(ctx["bot"])


async def shutdown(ctx):
    bot = ctx.get("bot")
    if bot is not None:
        await bot.session.close()


class WorkerSettings:
    functions = [execute_job]
    cron_jobs = [
        cron(refunds, second={12, 32, 52}, run_at_startup=True),
        cron(expire_invoices, second={17, 37, 57}, run_at_startup=True),
        cron(deliver_confirmations, second={5, 25, 45}),
        cron(cleanup_terminal_files, second={0, 20, 40}, run_at_startup=True),
        cron(cleanup, minute={0, 15, 30, 45}),
        cron(deliver_failures, second={10, 30, 50}),
        cron(flush_reports, minute=set(range(60)), second=15),
        cron(daily_report, hour=config().report_hour, minute=config().report_minute),
        cron(dispatch, second=set(range(0, 60, 5)), run_at_startup=True),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(config().redis_url.get_secret_value())
    timezone = ZoneInfo("Asia/Riyadh")
    job_timeout = 480
    keep_result = 0
    max_jobs = 10
    health_check_interval = 15
