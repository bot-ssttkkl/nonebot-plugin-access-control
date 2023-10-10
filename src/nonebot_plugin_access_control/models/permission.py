from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class PermissionOrm(MappedAsDataclass, Model):
    __tablename__ = "accctrl_permission"
    __table_args__ = {"extend_existing": True}

    subject: Mapped[str] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(primary_key=True)
    allow: Mapped[bool]
