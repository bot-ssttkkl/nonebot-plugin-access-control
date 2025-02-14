import nonebot
from nonebot.adapters.console import Adapter as ConsoleAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ConsoleAdapter)

nonebot.load_plugin("nonebot_plugin_ac_demo")
nonebot.load_plugin("nonebot_plugin_access_control")

if __name__ == "__main__":
    nonebot.run()
