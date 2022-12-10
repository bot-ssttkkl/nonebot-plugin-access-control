from sqlalchemy import Column, String, Boolean

from .data_source import data_source


@data_source.registry.mapped
class PermissionOrm:
    __tablename__ = 'permissions'

    subject: str = Column(String, nullable=False, primary_key=True)
    service: str = Column(String, nullable=False, primary_key=True)
    allow: bool = Column(Boolean, nullable=False)
