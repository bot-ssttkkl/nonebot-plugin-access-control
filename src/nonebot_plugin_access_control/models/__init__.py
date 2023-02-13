from sqlmodel import SQLModel, Field


class PermissionOrm(SQLModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_permission'
    __table_args__ = {"extend_existing": True}

    subject: str = Field(primary_key=True)
    service: str = Field(primary_key=True)
    allow: bool


class RateLimitRuleOrm(SQLModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_rate_limit_rule'
    __table_args__ = {"extend_existing": True}

    id: int = Field(primary_key=True)
    subject: str
    service: str
    limit: int
    time_span: int
