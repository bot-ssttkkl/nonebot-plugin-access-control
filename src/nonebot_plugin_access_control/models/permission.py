from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass


class PermissionOrm(MappedAsDataclass, Model):
    __tablename__ = 'nonebot_plugin_access_control_permission'
    __table_args__ = {"extend_existing": True}

    subject: Mapped[str] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(primary_key=True)
    allow: Mapped[bool]
