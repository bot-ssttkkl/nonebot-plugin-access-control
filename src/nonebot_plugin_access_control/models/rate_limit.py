from enum import Enum

from sqlmodel import SQLModel, Field


class LimitFor(int, Enum):
    user = 0
    subject = 1


class RateLimitRuleOrm(SQLModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_rule'
    __table_args__ = {"extend_existing": True}

    id: int = Field(primary_key=True)
    subject: str
    service: str
    time_span: int
    limit: int
    limit_for: LimitFor
