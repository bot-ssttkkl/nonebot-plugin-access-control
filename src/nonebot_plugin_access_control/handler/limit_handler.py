from typing import TextIO, Optional

import pytimeparser

from nonebot_plugin_access_control_api.models.rate_limit import RateLimitRule
from nonebot_plugin_access_control_api.service import Service
from nonebot_plugin_access_control_api.service.methods import (
    get_service_by_qualified_name,
)
from nonebot_plugin_access_control_api.errors import (
    AccessControlQueryError,
    AccessControlBadRequestError,
)

from .utils.permission import require_superuser_or_script


def _map_rule(f: TextIO, rule: RateLimitRule, service_name: Optional[str]):
    f.write(
        f"[{rule.id}] 服务 '{rule.service.qualified_name}' "
        f"限制主体 '{rule.subject}' "
        f"每 {int(rule.time_span.total_seconds())} 秒钟"
        f"最多调用 {rule.limit} 次 "
    )
    if rule.overwrite:
        f.write(" (覆写)")
    if service_name is not None and rule.service.qualified_name != service_name:
        f.write(f" (继承自服务 '{rule.service.qualified_name}')")


@require_superuser_or_script
async def add(
    f: TextIO,
    service_name: Optional[str],
    subject: Optional[str],
    limit: Optional[int],
    time_span: Optional[str],
    overwrite: Optional[bool],
):
    if not subject or not service_name:
        raise AccessControlBadRequestError("请指定服务名（--service）与主体（--subject）")
    elif not time_span:
        raise AccessControlBadRequestError("请指定限制时间段（--span）")
    elif not limit:
        raise AccessControlBadRequestError("请指定限制次数（--limit）")
    elif limit <= 0:
        raise AccessControlBadRequestError("限制次数（--limit）必须大于0")

    try:
        parsed_time_span = pytimeparser.parse(time_span)
    except ValueError:
        raise AccessControlBadRequestError("给定的限制时间段（--span）不合法")

    service = get_service_by_qualified_name(service_name)
    if service is None:
        raise AccessControlQueryError(f"找不到服务 {service_name}")

    rule = await service.add_rate_limit_rule(
        subject, parsed_time_span, limit, overwrite or False
    )
    _map_rule(f, rule, service_name)


@require_superuser_or_script
async def rm(
    f: TextIO,
    rule_id: Optional[str],
):
    if not rule_id:
        raise AccessControlBadRequestError("请指定限流规则ID")

    ok = await Service.remove_rate_limit_rule(rule_id)
    if ok:
        f.write("删除成功")
    else:
        raise AccessControlQueryError("删除失败，未找到该限流规则")


@require_superuser_or_script
async def ls(f: TextIO, service_name: Optional[str], subject: Optional[str]):
    if not service_name and not subject:
        rules = [x async for x in Service.get_all_rate_limit_rules()]
    elif not service_name:
        rules = [x async for x in Service.get_all_rate_limit_rules_by_subject(subject)]
    else:
        service = get_service_by_qualified_name(service_name, raise_on_not_exists=True)

        if not subject:
            rules = [x async for x in service.get_rate_limit_rules()]
        else:
            rules = [x async for x in service.get_rate_limit_rules_by_subject(subject)]

    if len(rules) != 0:
        # 按照服务全称、subject排序
        rules = sorted(rules, key=lambda x: (x.service.qualified_name, x.subject, x.id))

        for rule in rules:
            _map_rule(f, rule, service_name)
            f.write("\n")
    else:
        f.write("无")


@require_superuser_or_script
async def reset(
    f: TextIO,
):
    await Service.clear_rate_limit_tokens()
    f.write("成功")
