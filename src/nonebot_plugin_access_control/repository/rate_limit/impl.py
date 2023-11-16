from typing import Optional
from datetime import timedelta
from collections.abc import AsyncGenerator

from sqlalchemy import func, select

from nonebot_plugin_access_control_api.context import context
from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.errors import AccessControlQueryError
from nonebot_plugin_access_control_api.models.rate_limit import RateLimitRule
from nonebot_plugin_access_control_api.service.interface.nonebot_service import (
    INoneBotService,
)

from ..utils import use_ac_session
from .interface import IRateLimitRepository
from ..orm.rate_limit import RateLimitRuleOrm


@context.bind_singleton_to(IRateLimitRepository)
class RateLimitRepository(IRateLimitRepository):
    async def get_rules_by_subject(
        self, service: Optional[IService], subject: Optional[str]
    ) -> AsyncGenerator[RateLimitRuleOrm, None]:
        async with use_ac_session() as session:
            stmt = select(RateLimitRuleOrm)
            if service is not None:
                stmt = stmt.where(RateLimitRuleOrm.service == service.qualified_name)
            if subject is not None:
                stmt = stmt.where(RateLimitRuleOrm.subject == subject)

            async for x in await session.stream_scalars(stmt):
                s = service
                if s is None:
                    s = context.require(INoneBotService).get_service_by_qualified_name(
                        x.service
                    )
                if s is not None:
                    yield RateLimitRule(
                        x.id,
                        s,
                        x.subject,
                        timedelta(seconds=x.time_span),
                        x.limit,
                        x.overwrite,
                    )

    async def add_rate_limit_rule(
        self,
        service: IService,
        subject: str,
        time_span: timedelta,
        limit: int,
        overwrite: bool = False,
    ) -> RateLimitRule:
        async with use_ac_session() as sess:
            if overwrite:
                stmt = select(func.count()).where(
                    RateLimitRuleOrm.subject == subject,
                    RateLimitRuleOrm.service == service.qualified_name,
                )
                cnt = (await sess.execute(stmt)).scalar_one()

                if cnt > 0:
                    raise AccessControlQueryError("已存在对该实体与服务的限流规则，不允许再添加覆写规则")

            orm = RateLimitRuleOrm(
                subject=subject,
                service=service.qualified_name,
                time_span=int(time_span.total_seconds()),
                limit=limit,
                overwrite=overwrite,
            )
            sess.add(orm)
            await sess.commit()

            await sess.refresh(orm)

            rule = RateLimitRule(orm.id, service, subject, time_span, limit, overwrite)

            return rule

    async def remove_rate_limit_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        async with use_ac_session() as sess:
            orm = await sess.get(RateLimitRuleOrm, rule_id)
            if orm is None:
                return None

            await sess.delete(orm)
            await sess.commit()

            service = context.require(INoneBotService).get_service_by_qualified_name(
                orm.service
            )

            rule = RateLimitRule(
                orm.id,
                service,
                orm.subject,
                timedelta(seconds=orm.time_span),
                orm.limit,
                orm.overwrite,
            )

            return rule
