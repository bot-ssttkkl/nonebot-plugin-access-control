from typing import TextIO
from contextlib import asynccontextmanager

from nonebot import logger
from arclet.alconna import Arparma
from arclet.alconna.typing import DataCollection
from ssttkkl_nonebot_utils.errors.error_handler import ErrorHandlers

from nonebot_plugin_access_control_api.errors import (
    PermissionDeniedError,
    AccessControlBadRequestError,
)

from ..alc import alc_ac
from ..config import conf
from . import (
    help_handler,
    limit_handler,
    service_handler,
    subject_handler,
    permission_handler,
)

error_handlers = ErrorHandlers()


@error_handlers.register(PermissionDeniedError)
def _handle_permission_denied(e: PermissionDeniedError):
    if not conf().access_control_reply_on_permission_denied_enabled:
        return None
    return conf().access_control_reply_on_permission_denied


@asynccontextmanager
async def _handing_error(fout: TextIO):
    try:
        async with error_handlers.run_excepting(fout.write, reraise_unhandled=True):
            yield
    except BaseException as e:
        logger.exception(e)


async def handle_ac(fout: TextIO, cmd: str):
    async with _handing_error(fout):
        result = alc_ac.parse(cmd)

        if result.matched:
            if result.find("permission"):
                await _handle_permission(fout, result)
            elif result.find("limit"):
                await _handle_limit(fout, result)
            elif result.find("service"):
                await _handle_service(fout, result)
            elif result.find("subject"):
                await _handle_subject(fout, result)
            elif result.find("help"):
                await _handle_help(fout, result)
            else:
                raise AccessControlBadRequestError("不存在该命令")
        else:
            raise AccessControlBadRequestError("命令格式错误")


async def _handle_permission(fout: TextIO, result: Arparma[DataCollection]):
    ls = result.query("permission.ls")
    allow = result.query("permission.allow")
    deny = result.query("permission.deny")
    rm = result.query("permission.rm")

    if ls:
        await permission_handler.ls(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
        )
    elif allow:
        await permission_handler.set_(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
            True,
        )
    elif deny:
        await permission_handler.set_(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
            False,
        )
    elif rm:
        await permission_handler.rm(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
        )
    else:
        raise AccessControlBadRequestError("命令格式错误")


async def _handle_limit(fout: TextIO, result: Arparma[DataCollection]):
    add = result.query("limit.add")
    rm = result.query("limit.rm")
    ls = result.query("limit.ls")
    reset = result.query("limit.reset")

    if add:
        await limit_handler.add(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
            result.all_matched_args.get("limit"),
            result.all_matched_args.get("span"),
            result.query("limit.add.overwrite", False).value,
        )
    elif rm:
        await limit_handler.rm(
            fout,
            result.all_matched_args.get("limit_rule_id"),
        )
    elif ls:
        await limit_handler.ls(
            fout,
            result.all_matched_args.get("service"),
            result.all_matched_args.get("subject"),
        )
    elif reset:
        await limit_handler.reset(
            fout,
        )
    else:
        raise AccessControlBadRequestError("命令格式错误")


async def _handle_service(fout: TextIO, result: Arparma[DataCollection]):
    ls = result.query("service.ls")

    if ls:
        await service_handler.ls(
            fout,
            result.all_matched_args.get("service"),
        )
    else:
        raise AccessControlBadRequestError("命令格式错误")


async def _handle_subject(fout: TextIO, result: Arparma[DataCollection]):
    await subject_handler.subject(fout)


async def _handle_help(fout: TextIO, result: Arparma[DataCollection]):
    await help_handler.help(fout)


__all__ = ("handle_ac",)
