from functools import wraps

from nonebot import logger
from nonebot.exception import MatcherException
from nonebot.internal.matcher import current_matcher

from ..errors import RbacError


def handle_error(silently: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapped_func(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MatcherException as e:
                raise e
            except RbacError as e:
                logger.exception(e)
                if not silently:
                    matcher = current_matcher.get()
                    await matcher.finish(f"{str(e)}")
            except Exception as e:
                logger.exception(e)
                if not silently:
                    matcher = current_matcher.get()
                    await matcher.finish(f"内部错误：{type(e)}{str(e)}")

        return wrapped_func

    return decorator
