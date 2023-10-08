from typing import TextIO

from .utils.env import ac_get_env
from .utils.permission import require_superuser_or_script
from ..alc import help_ac


@require_superuser_or_script
async def help(f: TextIO):
    f.write(help_ac(ac_get_env()))
