from nonebot import require

require("nonebot_plugin_datastore")

from . import access_control
from . import config
from . import errors
from . import event_bus
from . import matchers
from . import models
from . import service
from . import subject
from . import utils

from importlib import import_module
from nonebot import logger, get_driver

supported_modules = {
    "OneBot V11": "nonebot_plugin_access_control_onebot",
    "OneBot V12": "nonebot_plugin_access_control_onebot",
    "Kaiheila": "nonebot_plugin_access_control_kaiheila",
}

loaded_modules = []

driver = get_driver()
for adapter in driver._adapters:
    if adapter in supported_modules:
        import_module(supported_modules[adapter])
        loaded_modules.append(adapter)
        logger.debug(f"Succeed to loaded plugin for {adapter}")

if len(loaded_modules):
    logger.success(f"Loaded plugin for: {', '.join(loaded_modules)}")
