from sys import stdin, stdout
from importlib.metadata import version

import anyio
from nb_cli import run_sync
from nb_cli.cli import run_async
from nonebot_plugin_orm import init_orm

from ..handler import handle_ac
from .. import __plugin_meta__ as plugin_meta
from ..handler.utils.env import ac_set_script_env

welcome_text = f"""
nonebot-plugin-access-control v{version("nonebot_plugin_access_control")}
{plugin_meta.homepage}

输入 \'help\' 获取帮助
""".strip()
welcome_text = "\n\n" + welcome_text + "\n"


@run_async
async def main():
    await init_orm()
    print(welcome_text)
    while True:
        print("> ", end="", flush=True)
        cmd = stdin.readline().strip()
        if cmd == "exit":
            return
        elif cmd == "clear":
            for i in range(50):
                print()
        elif cmd == "":
            continue
        else:
            await handle_ac(stdout, "ac " + cmd)
            stdout.write("\n")


def install():
    ac_set_script_env()
    anyio.run(run_sync(main))
