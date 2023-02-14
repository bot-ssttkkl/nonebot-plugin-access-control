from typing import Optional, AsyncGenerator, Tuple

from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Service
from .nonebot import NoneBotService
from .plugin import PluginService
from ..models import PermissionOrm

_nonebot_service = NoneBotService()


def get_nonebot_service() -> NoneBotService:
    return _nonebot_service


def create_plugin_service(plugin_name: str) -> PluginService:
    return get_nonebot_service().create_plugin_service(plugin_name)


def get_plugin_service(plugin_name: str) -> Optional[PluginService]:
    return get_nonebot_service().get_plugin_service(plugin_name)


def get_service_by_qualified_name(qualified_name: str) -> Optional[Service]:
    return get_nonebot_service().get_service_by_qualified_name(qualified_name)


async def get_services_by_subject(subject: str) -> AsyncGenerator[Tuple[Service, bool], None]:
    async with AsyncSession(get_engine()) as session:
        stmt = select(PermissionOrm).where(PermissionOrm.subject == subject)
        async for x in await session.stream_scalars(stmt):
            service = get_service_by_qualified_name(x.service)
            if service is not None:
                yield service, x.allow


async def get_all_permissions() -> AsyncGenerator[Tuple[Service, bool, str], None]:
    async with AsyncSession(get_engine()) as session:
        stmt = select(PermissionOrm)
        async for x in await session.stream_scalars(stmt):
            service = get_service_by_qualified_name(x.service)
            if service is not None:
                yield service, x.allow, x.subject


__all__ = ("get_nonebot_service",
           "create_plugin_service", "get_plugin_service",
           "get_service_by_qualified_name", "get_services_by_subject",
           "get_all_permissions")
