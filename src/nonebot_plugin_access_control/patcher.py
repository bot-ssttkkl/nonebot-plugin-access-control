from nonebot import logger, get_driver, get_loaded_plugins

from nonebot_plugin_access_control_api.service.methods import get_nonebot_service

from .config import conf

if conf().access_control_auto_patch_enabled:

    @get_driver().on_startup
    def _():
        nonebot_service = get_nonebot_service()

        patched_plugins = []

        for plugin in get_loaded_plugins():
            if (
                plugin.name == "nonebot_plugin_access_control"
                or plugin.name in conf().access_control_auto_patch_ignore
            ):
                continue

            service = nonebot_service.get_or_create_plugin_service(plugin.name)
            if service.auto_created:
                for matcher in plugin.matcher:
                    service.patch_matcher(matcher)
                patched_plugins.append(plugin)

        logger.opt(colors=True).success(
            "auto patched plugin(s): "
            + ", ".join([f"<y>{p.name}</y>" for p in patched_plugins])
        )
