from nonebot import logger

from nonebot_plugin_access_control.service import Service
from nonebot_plugin_access_control.service.permission import Permission
from nonebot_plugin_access_control.service.rate_limit import RateLimitRule

from .plugin_service import plugin_service
from .matcher_demo import a_service, b_service, c_service


@plugin_service.on_set_permission
async def _(service: Service, permission: Permission):
    logger.debug(
        f"on set permission: {service} {permission.subject}, "
        f"now allow={permission.allow}"
    )


@plugin_service.on_remove_permission
async def _(service: Service, subject: str):
    allow = await service.get_permission_by_subject(subject)
    logger.debug(f"on remove permission: {service} {subject}, " f"now allow={allow}")


@a_service.on_change_permission
@b_service.on_change_permission
@c_service.on_change_permission
async def _(service: Service, permission: Permission):
    logger.debug(
        f"on change permission: {service} {permission.subject}, "
        f"now allow={permission.allow}"
    )


@a_service.on_add_rate_limit_rule
@b_service.on_add_rate_limit_rule
@c_service.on_add_rate_limit_rule
async def _(service: Service, rule: RateLimitRule):
    logger.debug(f"on add rate limit rule: #{rule.id} {service} {rule.subject}")


@a_service.on_remove_rate_limit_rule
@b_service.on_remove_rate_limit_rule
@c_service.on_remove_rate_limit_rule
async def _(service: Service, rule: RateLimitRule):
    logger.debug(f"on remove rate limit rule: #{rule.id} {service} {rule.subject}")
