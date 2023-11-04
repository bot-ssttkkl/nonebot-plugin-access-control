"""data_migrate

修订 ID: 96ced46e72e9
父修订: 9bb3231cf9aa
创建时间: 2023-10-11 21:07:26.511220

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect
from alembic.op import run_async
from nonebot import logger, require
from pkg_resources import DistributionNotFound, get_distribution
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection

revision: str = "96ced46e72e9"
down_revision: str | Sequence[str] | None = "9bb3231cf9aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


async def data_migrate(conn: AsyncConnection):
    require("nonebot_plugin_datastore")

    from nonebot_plugin_datastore.db import get_engine

    # nonebot_plugin_access_control_permission
    async with AsyncConnection(get_engine()) as ds_conn:
        async with AsyncSession(ds_conn) as ds_sess:
            if not await ds_conn.run_sync(
                lambda conn: inspect(conn).has_table(
                    "nonebot_plugin_access_control_alembic_version"
                )
            ):
                return

            result = (
                await ds_sess.execute(
                    sa.text(
                        "SELECT version_num "
                        "FROM nonebot_plugin_access_control_alembic_version"
                    )
                )
            ).scalar_one_or_none()
            if result != "6fbda6d1d8ee":
                raise RuntimeError(
                    "请先执行 nb datastore upgrade "
                    "--name nonebot_plugin_access_control "
                    "将旧数据库迁移到最新版本"
                )

            result = await ds_sess.stream(
                sa.text(
                    "SELECT subject, service, allow "
                    "FROM nonebot_plugin_access_control_permission;"
                )
            )
            async for row in result:
                subject, service, allow = row
                await conn.execute(
                    sa.text(
                        "INSERT INTO accctrl_permission (subject, service, allow) "
                        "VALUES (:subject, :service, :allow);"
                    ),
                    [{"subject": subject, "service": service, "allow": allow}],
                )
                logger.debug(
                    f"从表 nonebot_plugin_access_control_permission 迁移数据："
                    f"subject={subject} service={service} allow={allow}"
                )

            # nonebot_plugin_access_control_rate_limit_rule
            result = await ds_sess.stream(
                sa.text(
                    "SELECT id, subject, service, time_span, `limit`, overwrite "
                    "FROM nonebot_plugin_access_control_rate_limit_rule;"
                )
            )
            async for row in result:
                id, subject, service, time_span, limit, overwrite = row
                await conn.execute(
                    sa.text(
                        "INSERT INTO accctrl_rate_limit_rule (id, subject, service, time_span, `limit`, overwrite) "
                        "VALUES (:id, :subject, :service, :time_span, :limit, :overwrite);"
                    ),
                    [
                        {
                            "id": id,
                            "subject": subject,
                            "service": service,
                            "time_span": time_span,
                            "limit": limit,
                            "overwrite": overwrite,
                        }
                    ],
                )
                logger.debug(
                    f"从表 nonebot_plugin_access_control_rate_limit_rule 迁移数据："
                    f"id={id} subject={subject} service={service} "
                    f"time_span={time_span} limit={limit} overwrite={overwrite}"
                )

            # nonebot_plugin_access_control_rate_limit_token
            result = await ds_sess.stream(
                sa.text(
                    "SELECT id, rule_id, `user`, acquire_time, expire_time "
                    "FROM nonebot_plugin_access_control_rate_limit_token;"
                )
            )
            async for row in result:
                id, rule_id, user, acquire_time, expire_time = row
                await conn.execute(
                    sa.text(
                        "INSERT INTO accctrl_rate_limit_rule (id, rule_id, `user`, acquire_time, expire_time) "
                        "VALUES (:id, :rule_id, :user, :acquire_time, :expire_time);"
                    ),
                    [
                        {
                            "id": id,
                            "rule_id": rule_id,
                            "user": user,
                            "acquire_time": acquire_time,
                            "expire_time": expire_time,
                        }
                    ],
                )
                logger.debug(
                    f"从表 nonebot_plugin_access_control_rate_limit_token 迁移数据："
                    f"id={id} rule_id={rule_id} user={user} "
                    f"acquire_time={acquire_time} expire_time={expire_time}"
                )


def upgrade(name: str = "") -> None:
    if name:
        return
    try:
        get_distribution("nonebot_plugin_datastore")
    except DistributionNotFound:
        return

    logger.info("正在从 datastore 迁移数据……")
    run_async(data_migrate)


def downgrade(name: str = "") -> None:
    # do nothing
    pass
