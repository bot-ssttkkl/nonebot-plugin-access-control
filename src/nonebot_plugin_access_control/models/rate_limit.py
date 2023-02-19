from datetime import datetime
from typing import Optional, List

from shortuuid import ShortUUID
from sqlalchemy import Index
from sqlmodel import Field, Relationship

from nonebot_plugin_access_control.plugin_data import PluginModel

_shortuuid = ShortUUID(alphabet="23456789abcdefghijkmnopqrstuvwxyz")


def _gen_id():
    return _shortuuid.random(length=5)


class RateLimitRuleOrm(PluginModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_rule'
    __table_args__ = (
        Index("ix_nonebot_plugin_access_control_rate_limit_rule_subject_service", "subject", "service"),
        {
            "extend_existing": True
        }
    )

    id: str = Field(default_factory=_gen_id, primary_key=True)
    subject: str
    service: str
    time_span: int  # 单位：秒
    limit: int
    overwrite: bool

    tokens: List["RateLimitTokenOrm"] = Relationship(back_populates="rule",
                                                     sa_relationship_kwargs={"cascade": "delete"})


class RateLimitTokenOrm(PluginModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_token'
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: str = Field(foreign_key='nonebot_plugin_access_control_rate_limit_rule.id', index=True)
    user: str
    acquire_time: datetime = Field(default_factory=datetime.utcnow)

    rule: RateLimitRuleOrm = Relationship(back_populates="tokens")
