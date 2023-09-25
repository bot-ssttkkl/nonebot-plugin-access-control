nonebot-plugin-access-control for QQ Guild
========

## 主体定义

从上往下优先级从高到低

| 主体                                              | TAG                                 | 含义          | 示例                                         | 存在条件                  |
|-------------------------------------------------|-------------------------------------|-------------|--------------------------------------------|-----------------------|
| qqguild:g<guild_id>:c<channel_id>:<user_id>     | platform:guild:channel:user         | 服务器频道用户     | qqguild:g87654321:c123454321:12345678      | 仅当消息来自频道时存在           |
| qqguild:c<channel_id>:<user_id>                 | platform:channel:user               | 频道用户        | qqguild:c123454321:12345678                | 仅当消息来自频道时存在           |
| qqguild:g<guild_id>:<user_id>                   | platform:guild:user                 | 服务器用户       | qqguild:g87654321:12345678                 | 仅当消息来自频道时存在           |
| qqguild:<user_id>                               | platform:user                       | 用户          | qqguild:12345678                           |                       |
| superuser                                       | superuser                           | 超级用户        |                                            | 仅当该用户为超级用户时存在         |
| qqguild:g<guild_id>.guild_owner                 | qqguild:guild.guild_owner           | 服务器主        | qqguild:g87654321.guild_owner              | 仅当消息来自频道、该用户为服务器主时存在  |
| qqguild:guild_owner                             | qqguild:guild_owner                 | 服务器主        |                                            | 仅当消息来自频道、该用户为服务器主时存在  |
| qqguild:g<guild_id>.guild_admin                 | qqguild:guild.guild_admin           | 服务器管理       | qqguild:g87654321.guild_admin              | 仅当消息来自频道、该用户为服务器管理时存在 |
| qqguild:guild_admin                             | qqguild:guild_admin                 | 服务器管理       |                                            | 仅当消息来自频道、该用户为服务器管理时存在 |
| qqguild:g<guild_id>:c<channel_id>.channel_admin | qqguild:guild:channel.channel_admin | 频道管理        | qqguild:g87654321:c123454321.channel_admin | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:c<channel_id>.channel_admin             | qqguild:channel.channel_admin       | 频道管理        | qqguild:c123454321.channel_admin           | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:channel_admin                           | qqguild:channel_admin               | 频道管理        |                                            | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:g<guild_id>.role_\<rold_id\>            | qqguild:guild.role                  | 服务器身份组      | qqguild:g87654321.role_233                 | 仅当消息来自频道、该用户在该身份组时存在  |
| qqguild:g<guild_id>:c<channel_id>               | platform:guild:channel              | 服务器频道       | qqguild:g87654321:c123454321               | 仅当消息来自频道时存在           |
| qqguild:c<channel_id>                           | platform:channel                    | 频道          | qqguild:c123454321                         | 仅当消息来自频道时存在           |
| qqguild:g<guild_id>                             | platform:guild                      | 服务器         | qqguild:g87654321                          | 仅当消息来自频道时存在           |
| qqguild:private                                 | platform:private                    | 来自QQ频道的私聊消息 |                                            | 仅当消息来自私聊时存在           |
| private                                         | private                             | 私聊消息        |                                            | 仅当消息来自私聊时存在           |                                        |                      |
| qqguild:channel                                 | platform:channel                    | 来自QQ频道的频道消息 |                                            | 仅当消息来自频道时存在           |
| channel                                         | channel                             | 频道消息        |                                            | 仅当消息来自频道是存在           |
| qqguild                                         | platform                            | 来自QQ频道的用户   |                                            |                       |
| all                                             | all                                 | 所有用户        |                                            |                       |
