from io import StringIO

import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_service_ls_handler(app: App):
    from nonebot_plugin_access_control.handler.service_handler import ls
    from nonebot_plugin_access_control.handler.utils.env import ac_set_script_env

    ac_set_script_env()

    EXPECTED = (
        "nonebot_plugin_ac_demo\n"
        "├── group1\n"
        "│   ├── a\n"
        "│   └── b\n"
        "├── c\n"
        "└── tick"
    )

    with StringIO() as f:
        await ls(f, "nonebot_plugin_ac_demo")

        res = f.getvalue()
        assert res.strip() == EXPECTED
