from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class RateLimitRuleOrm(SQLModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_rule'
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    service: str
    time_span: int  # 单位：秒
    limit: int

    tokens: List["RateLimitTokenOrm"] = Relationship(back_populates="rule")


class RateLimitTokenOrm(SQLModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_token'
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key='nonebot_plugin_access_control_rate_limit_rule.id')
    user: Optional[str]
    acquire_time: datetime = Field(default_factory=datetime.utcnow)

    rule: RateLimitRuleOrm = Relationship(back_populates="tokens")
