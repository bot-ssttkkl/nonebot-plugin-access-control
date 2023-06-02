nonebot-plugin-access-control for QQ Guild
========

（暂时未对私聊进行测试）

## 主体定义

从上往下优先级从高到低

| 主体                                          | 含义      | 示例                                    | 必定存在          |
|---------------------------------------------|---------|---------------------------------------|---------------|
| qqguild:g<guild_id>:c<channel_id>:<user_id> | 服务器频道用户 | qqguild:g87654321:c123454321:12345678 | 仅当消息来自频道时存在   |
| qqguild:c<channel_id>:<user_id>             | 频道用户    | qqguild:c123454321:12345678           | 仅当消息来自频道时存在   |
| qqguild:g<guild_id>:<user_id>               | 服务器用户   | qqguild:g87654321:12345678            | 仅当消息来自服务器时存在  |
| qqguild:<user_id>                           | 用户      | qqguild:12345678                      | 是             |
| superuser                                   | 超级用户    |                                       | 仅当该用户为超级用户时存在 |
| qqguild:g<guild_id>:c<channel_id>           | 服务器频道   | qqguild:g87654321:c123454321          | 仅当消息来自频道时存在   |
| qqguild:c<channel_id>                       | 频道      | qqguild:c123454321                    | 仅当消息来自频道时存在   |
| qqguild:g<guild_id>                         | 服务器     | qqguild:g87654321                     | 仅当消息来自频道时存在   |
| qqguild:private                             | 私聊消息    | qq:private                            | 仅当消息来自私聊时存在   |
| qqguild:channel                             | 频道消息    | qqguild:channel                       | 仅当消息来自频道时存在   |
| qqguild                                     | 某个平台用户  | qq                                    | 是             |
| all                                         | 所有用户    |                                       | 是             |
