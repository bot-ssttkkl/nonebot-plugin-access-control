from sqlmodel import Field

from nonebot_plugin_access_control.plugin_data import PluginModel


class PermissionOrm(PluginModel, table=True):
    __tablename__ = 'nonebot_plugin_access_control_permission'
    __table_args__ = {"extend_existing": True}

    subject: str = Field(primary_key=True)
    service: str = Field(primary_key=True)
    allow: bool
