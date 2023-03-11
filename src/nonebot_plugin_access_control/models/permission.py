from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass

from nonebot_plugin_access_control.plugin_data import plugin_data


class PermissionOrm(MappedAsDataclass, plugin_data.Model):
    __tablename__ = 'nonebot_plugin_access_control_permission'
    __table_args__ = {"extend_existing": True}

    subject: Mapped[str] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(primary_key=True)
    allow: Mapped[bool]
