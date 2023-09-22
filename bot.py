import nonebot

from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

nonebot.load_plugin("nonebot_plugin_access_control")
nonebot.load_plugin("nonebot_plugin_ac_demo")

if __name__ == "__main__":
    nonebot.run()
