from io import StringIO
from datetime import timedelta
from collections.abc import Collection
from typing import TYPE_CHECKING, Optional

import pytest
from nonebug import App

if TYPE_CHECKING:
    from nonebot_plugin_access_control_api.models.rate_limit import RateLimitRule


def check_ls_res(
    res: str, rule: Collection["RateLimitRule"], service_name: Optional[str]
):
    from nonebot_plugin_access_control.handler.limit_handler import _map_rule

    res = res.split("\n")
    for i, s in enumerate(res):
        res[i] = s.strip()

    for r in rule:
        with StringIO() as f:
            _map_rule(f, r, service_name)
            rule_text = f.getvalue().strip()
        assert rule_text in res


@pytest.mark.asyncio
async def test_limit_handler(app: App):
    from nonebot_plugin_access_control_api.service import get_service_by_qualified_name

    from nonebot_plugin_access_control.handler.limit_handler import ls, rm, add
    from nonebot_plugin_access_control.handler.utils.env import ac_set_script_env

    ac_set_script_env()

    # add
    rule_id = ["", ""]
    with StringIO() as f:
        await add(f, "nonebot_plugin_ac_demo", "all", 3, "1m", False)
        res = f.getvalue().strip()
        rule_id[0] = res[1:6]
    with StringIO() as f:
        await add(f, "nonebot_plugin_ac_demo.group1", "qq:23456", 5, "30s", True)
        res = f.getvalue().strip()
        rule_id[1] = res[1:6]

    rules = [
        x
        async for x in get_service_by_qualified_name(
            "nonebot_plugin_ac_demo.group1"
        ).get_rate_limit_rules()
    ]
    assert len(rules) == 2

    rule = [None, None]
    for x in rules:
        idx = rule_id.index(x.id)
        if idx != -1:
            rule[idx] = x

    assert rule[0].service.qualified_name == "nonebot_plugin_ac_demo"
    assert rule[0].subject == "all"
    assert rule[0].limit == 3
    assert rule[0].time_span == timedelta(minutes=1)
    assert rule[0].overwrite is False

    assert rule[1].service.qualified_name == "nonebot_plugin_ac_demo.group1"
    assert rule[1].subject == "qq:23456"
    assert rule[1].limit == 5
    assert rule[1].time_span == timedelta(seconds=30)
    assert rule[1].overwrite is True

    # ls (service_name=None, subject=None)
    with StringIO() as f:
        await ls(f, None, None)
        check_ls_res(f.getvalue(), rule, None)

    # ls (service_name=None, subject="all")
    with StringIO() as f:
        await ls(f, None, "all")
        check_ls_res(f.getvalue(), [rule[0]], None)

    # ls (service_name="nonebot_plugin_ac_demo.group1", subject=None)
    with StringIO() as f:
        await ls(f, "nonebot_plugin_ac_demo.group1", None)
        check_ls_res(f.getvalue(), rule, "nonebot_plugin_ac_demo.group1")

    # ls (service_name="nonebot_plugin_ac_demo.group1", subject="qq:23456")
    with StringIO() as f:
        await ls(f, "nonebot_plugin_ac_demo.group1", "qq:23456")
        check_ls_res(f.getvalue(), [rule[1]], "nonebot_plugin_ac_demo.group1")

    # rm
    with StringIO() as f:
        await rm(f, rule[0].id)

    # ls (service_name=None, subject=None)
    with StringIO() as f:
        await ls(f, None, None)
        check_ls_res(f.getvalue(), [rule[1]], None)
