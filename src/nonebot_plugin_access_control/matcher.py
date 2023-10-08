from io import StringIO

from nonebot import on_command
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg, CommandWhitespace

from .handler import handle_ac

cmd = on_command("ac")


async def send_multipart(matcher: Matcher, content: str):
    lines = content.split("\n")

    line_cnt = 0
    msg = ""
    for line in lines:
        msg += line
        msg += "\n"
        line_cnt += 1
        if line_cnt == 20:
            await matcher.send(msg.strip())
            line_cnt = 0
            msg = ""

    if line_cnt != 0:
        await matcher.send(msg.strip())


@cmd.handle()
async def handle_cmd(
    matcher: Matcher, cmd_space: str = CommandWhitespace(), cmd_body=CommandArg()
):
    if len(cmd_space) == 0:  # 避免指令撞车
        return

    cmd_body: str = cmd_body.extract_plain_text().strip()

    with StringIO() as f:
        await handle_ac(f, "ac " + cmd_body)
        await send_multipart(matcher, f.getvalue())
