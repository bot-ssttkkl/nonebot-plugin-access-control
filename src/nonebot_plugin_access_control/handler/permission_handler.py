from typing import TextIO, Optional

from nonebot_plugin_access_control_api.errors import (
    AccessControlQueryError,
    AccessControlBadRequestError,
)
from nonebot_plugin_access_control_api.models.permission import Permission
from nonebot_plugin_access_control_api.service import (
    get_service_by_qualified_name,
    Service,
)

from .utils.permission import require_superuser_or_script


def _map_permission(p: Permission, query_service_name: Optional[str] = None) -> str:
    s = f"'{p.service.qualified_name}'"

    if p.allow:
        s += " 允许 "
    else:
        s += " 拒绝 "

    s += f"'{p.subject}'"
    if (
        query_service_name is not None
        and p.service.qualified_name != query_service_name
    ):
        s += f" (继承自服务 '{p.service.qualified_name}')"

    return s


@require_superuser_or_script
async def set_(
    f: TextIO, service_name: Optional[str], subject: Optional[str], allow: bool
):
    if not subject or not service_name:
        raise AccessControlBadRequestError("请指定服务名（--service）与主体（--subject）")

    service = get_service_by_qualified_name(service_name, raise_on_not_exists=True)
    await service.set_permission(subject, allow)
    p = Permission(service, subject, allow)
    f.write(_map_permission(p))


@require_superuser_or_script
async def rm(f: TextIO, service_name: Optional[str], subject: Optional[str]):
    if not subject or not service_name:
        raise AccessControlBadRequestError("请指定服务名（--service）与主体（--subject）")

    service = get_service_by_qualified_name(service_name, raise_on_not_exists=True)
    ok = await service.remove_permission(subject)
    if ok:
        f.write("删除成功")
    else:
        raise AccessControlQueryError("删除失败，权限配置不存在")


@require_superuser_or_script
async def ls(f: TextIO, service_name: Optional[str], subject: Optional[str]):
    if not service_name and not subject:
        permissions = [x async for x in Service.get_all_permissions()]
    elif not service_name:
        permissions = [x async for x in Service.get_all_permissions_by_subject(subject)]
    else:
        service = get_service_by_qualified_name(service_name, raise_on_not_exists=True)
        if not subject:
            permissions = [x async for x in service.get_permissions()]
        else:
            permissions = [await service.get_permission_by_subject(subject)]

    if len(permissions) != 0:
        # 按照服务全称、先allow再deny、subject排序
        permissions = sorted(
            permissions, key=lambda x: (x.service.qualified_name, x.allow, x.subject)
        )

        for p in permissions:
            f.write(_map_permission(p, service_name))
            f.write("\n")
    else:
        f.write("无")
