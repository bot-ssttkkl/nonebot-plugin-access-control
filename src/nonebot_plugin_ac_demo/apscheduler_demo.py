from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import on_command, require, get_bot, Bot, logger
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher

from nonebot_plugin_ac_demo.plugin_service import plugin_service

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

tick_service = plugin_service.create_subservice("tick")
tick_matcher = tick_service.patch_matcher(on_command("tick"))


@tick_matcher.handle()
async def _(bot: Bot, matcher: Matcher, event: Event):
    args = event.get_message().extract_plain_text().split()[1:]
    if len(args) == 0:
        await matcher.finish("Usage: /tick {on, off}")
    elif args[0] == 'on':
        try:
            scheduler.add_job(job_handler,
                              IntervalTrigger(seconds=10),
                              kwargs={
                                  "bot_id": bot.self_id,
                                  "event": event
                              },
                              id=event.get_session_id())
            await matcher.finish("ok")
        except ConflictingIdError:
            await matcher.finish("ticker has already started")
    elif args[0] == 'off':
        try:
            scheduler.remove_job(event.get_session_id())
            await matcher.finish("ok")
        except JobLookupError:
            await matcher.finish("ticker hasn't started")


async def job_handler(bot_id: str, event: Event):
    # 传递bot的self_id而不是Bot实例，避免断开连接后Bot实例无法被回收导致资源泄露
    try:
        bot = get_bot(bot_id)
    except KeyError:
        logger.warning(f"bot {bot_id} not found")
        return

    if await tick_service.check(bot, event):
        await bot.send(event, "tick")
    else:
        logger.info("permission denied")
