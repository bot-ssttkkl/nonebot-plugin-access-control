from nonebot_plugin_access_control_api.context import context
from nonebot_plugin_access_control_api.service.interface import IService
from nonebot_plugin_access_control_api.service.interface.factory import (
    IServiceComponentFactory,
)
from nonebot_plugin_access_control_api.service.interface.patcher import IServicePatcher
from nonebot_plugin_access_control_api.service.interface.permission import (
    IServicePermission,
)
from nonebot_plugin_access_control_api.service.interface.rate_limit import (
    IServiceRateLimit,
)

from .patcher import ServicePatcherImpl
from .permission import ServicePermissionImpl
from .rate_limit import ServiceRateLimitImpl


@context.bind_singleton_to(IServiceComponentFactory)
class ServiceComponentFactory(IServiceComponentFactory):
    def create_patcher_impl(self, service: IService) -> IServicePatcher:
        return ServicePatcherImpl(service)

    def typeof_patcher_impl(self) -> type[IServicePatcher]:
        return ServicePatcherImpl

    def create_permission_impl(self, service: IService) -> IServicePermission:
        return ServicePermissionImpl(service)

    def typeof_permission_impl(self) -> type[IServicePermission]:
        return ServicePermissionImpl

    def create_rate_limit_impl(self, service: IService) -> IServiceRateLimit:
        return ServiceRateLimitImpl(service)

    def typeof_rate_limit_impl(self) -> type[IServiceRateLimit]:
        return ServiceRateLimitImpl
