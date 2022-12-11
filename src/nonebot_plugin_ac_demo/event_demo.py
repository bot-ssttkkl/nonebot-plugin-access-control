from nonebot import logger

from nonebot_plugin_access_control.service import Service
from .matcher_demo import a_service, b_service, c_service
from .plugin_service import plugin_service


@plugin_service.on_set_permission
async def _(service: Service, subject: str, allow: bool):
    logger.debug(f"on set permission: {service} {subject}, now allow={allow}")


@plugin_service.on_remove_permission
async def _(service: Service, subject: str):
    allow = await service.get_permission(subject)
    logger.debug(f"on remove permission: {service} {subject}, now allow={allow}")


@a_service.on_change_permission
@b_service.on_change_permission
@c_service.on_change_permission
async def _(service: Service, subject: str, allow: bool):
    logger.debug(f"on change permission: {service} {subject}, now allow={allow}")
