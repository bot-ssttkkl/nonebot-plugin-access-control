from io import StringIO
from collections.abc import Collection
from typing import TYPE_CHECKING, Optional

import pytest
from nonebug import App

if TYPE_CHECKING:
    from nonebot_plugin_access_control_api.models.permission import Permission


def check_ls_res(
    res: str, rule: Collection["Permission"], service_name: Optional[str] = None
):
    from nonebot_plugin_access_control.handler.permission_handler import _map_permission

    res = res.split("\n")
    for i, s in enumerate(res):
        res[i] = s.strip()

    for r in rule:
        rule_text = _map_permission(r, service_name).strip()
        assert rule_text in res


@pytest.mark.asyncio
async def test_permission_handler(app: App):
    from nonebot_plugin_access_control_api.service import get_service_by_qualified_name

    from nonebot_plugin_access_control.handler.utils.env import ac_set_script_env
    from nonebot_plugin_access_control.handler.permission_handler import ls, rm, set_

    ac_set_script_env()

    # set
    with StringIO() as f:
        await set_(f, "nonebot_plugin_ac_demo", "all", False)
    with StringIO() as f:
        await set_(f, "nonebot_plugin_ac_demo", "qq:23456", True)

    perm = [None, None]
    async for x in get_service_by_qualified_name(
        "nonebot_plugin_ac_demo"
    ).get_permissions():
        if x.subject == "all":
            perm[0] = x
        elif x.subject == "qq:23456":
            perm[1] = x

    assert perm[0].service.qualified_name == "nonebot_plugin_ac_demo"
    assert perm[0].subject == "all"
    assert perm[0].allow is False

    assert perm[1].service.qualified_name == "nonebot_plugin_ac_demo"
    assert perm[1].subject == "qq:23456"
    assert perm[1].allow is True

    # ls (service_name=None, subject=None)
    with StringIO() as f:
        await ls(f, None, None)
        check_ls_res(f.getvalue(), perm)

    # ls (service_name=None, subject="all")
    with StringIO() as f:
        await ls(f, None, "all")
        check_ls_res(f.getvalue(), [perm[0]])

    # ls (service_name="nonebot_plugin_ac_demo", subject=None)
    with StringIO() as f:
        await ls(f, "nonebot_plugin_ac_demo", None)
        check_ls_res(f.getvalue(), perm)

    # ls (service_name="nonebot_plugin_ac_demo", subject="qq:23456")
    with StringIO() as f:
        await ls(f, "nonebot_plugin_ac_demo", "qq:23456")
        check_ls_res(f.getvalue(), [perm[1]])

    # rm
    with StringIO() as f:
        await rm(f, perm[0].service.qualified_name, perm[0].subject)

    # ls (service_name=None, subject=None)
    with StringIO() as f:
        await ls(f, None, None)
        check_ls_res(f.getvalue(), [perm[1]])
