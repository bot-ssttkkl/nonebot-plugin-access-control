from datetime import datetime

from nonebot_plugin_orm import Model
from shortuuid import ShortUUID
from sqlalchemy import Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, MappedAsDataclass

_shortuuid = ShortUUID(alphabet="23456789abcdefghijkmnopqrstuvwxyz")


def _gen_id():
    return _shortuuid.random(length=5)


class RateLimitRuleOrm(MappedAsDataclass, Model):
    __tablename__ = "nonebot_plugin_access_control_rate_limit_rule"
    __table_args__ = (
        Index("ix_ac_rate_limit_rule_subject_service", "subject", "service"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(
        init=False, primary_key=True, default_factory=_gen_id
    )
    subject: Mapped[str]
    service: Mapped[str]
    time_span: Mapped[int]  # 单位：秒
    limit: Mapped[int]
    overwrite: Mapped[bool]

    tokens: Mapped[list["RateLimitTokenOrm"]] = relationship(
        init=False, back_populates="rule", cascade="delete"
    )


class RateLimitTokenOrm(MappedAsDataclass, Model):
    __tablename__ = "nonebot_plugin_access_control_rate_limit_token"
    __table_args__ = (
        Index("ix_ac_rate_limit_token_rule_id", "rule_id"),
        Index("ix_ac_rate_limit_token_expire_time", "expire_time"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    rule_id: Mapped[str] = mapped_column(
        ForeignKey("nonebot_plugin_access_control_rate_limit_rule.id")
    )
    user: Mapped[str]
    acquire_time: Mapped[datetime] = mapped_column()
    expire_time: Mapped[datetime] = mapped_column()

    rule: Mapped[RateLimitRuleOrm] = relationship(init=False, back_populates="tokens")
