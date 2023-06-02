nonebot-plugin-access-control for Kaiheila
========

## 主体定义

从上往下优先级从高到低

| 主体                                           | 含义      | 示例                                     | 必定存在          |
|----------------------------------------------|---------|----------------------------------------|---------------|
| kaiheila:g<guild_id>:c<channel_id>:<user_id> | 服务器频道用户 | kaiheila:g87654321:c123454321:12345678 | 仅当消息来自频道时存在   |
| kaiheila:c<channel_id>:<user_id>             | 频道用户    | kaiheila:c123454321:12345678           | 仅当消息来自频道时存在   |
| kaiheila:g<guild_id>:<user_id>               | 服务器用户   | kaiheila:g87654321:12345678            | 仅当消息来自服务器时存在  |
| kaiheila:<user_id>                           | 用户      | kaiheila:12345678                      | 是             |
| superuser                                    | 超级用户    |                                        | 仅当该用户为超级用户时存在 |
| kaiheila:g<guild_id>:c<channel_id>           | 服务器频道   | kaiheila:g87654321:c123454321          | 仅当消息来自频道时存在   |
| kaiheila:c<channel_id>                       | 频道      | kaiheila:c123454321                    | 仅当消息来自频道时存在   |
| kaiheila:g<guild_id>                         | 服务器     | kaiheila:g87654321                     | 仅当消息来自频道时存在   |
| kaiheila:private                             | 私聊消息    | qq:private                             | 仅当消息来自私聊时存在   |
| kaiheila:channel                             | 频道消息    | kaiheila:channel                       | 仅当消息来自频道时存在   |
| kaiheila                                     | 某个平台用户  | qq                                     | 是             |
| all                                          | 所有用户    |                                        | 是             |
