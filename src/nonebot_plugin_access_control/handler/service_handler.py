from typing import TextIO, Optional

from .utils.permission import require_superuser_or_script
from ..service import get_service_by_qualified_name
from ..utils.tree import get_tree_summary


@require_superuser_or_script
async def ls(f: TextIO, service_name: Optional[str]):
    service = get_service_by_qualified_name(service_name or "nonebot")
    summary = get_tree_summary(service, lambda x: x.children, lambda x: x.name)
    f.write(summary)
