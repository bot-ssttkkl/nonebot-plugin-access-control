from typing import TextIO

from .utils.env import get_env
from .utils.permission import require_superuser_or_script
from ..alc import help_ac


@require_superuser_or_script
async def help(
        f: TextIO
):
    f.write(help_ac(get_env()))
