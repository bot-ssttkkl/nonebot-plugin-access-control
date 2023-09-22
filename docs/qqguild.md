nonebot-plugin-access-control for QQ Guild
========

## 主体定义

从上往下优先级从高到低

| 主体                                              | 含义      | 示例                                         | 存在条件                  |
|-------------------------------------------------|---------|--------------------------------------------|-----------------------|
| qqguild:g<guild_id>:c<channel_id>:<user_id>     | 服务器频道用户 | qqguild:g87654321:c123454321:12345678      | 仅当消息来自频道时存在           |
| qqguild:c<channel_id>:<user_id>                 | 频道用户    | qqguild:c123454321:12345678                | 仅当消息来自频道时存在           |
| qqguild:g<guild_id>:<user_id>                   | 服务器用户   | qqguild:g87654321:12345678                 | 仅当消息来自频道时存在           |
| qqguild:<user_id>                               | 用户      | qqguild:12345678                           |                       |
| superuser                                       | 超级用户    |                                            | 仅当该用户为超级用户时存在         |
| qqguild:g<guild_id>.guild_owner                 | 服务器主    | qqguild:g87654321.guild_owner              | 仅当消息来自频道、该用户为服务器主时存在  |
| qqguild:guild_owner                             | 服务器主    |                                            | 仅当消息来自频道、该用户为服务器主时存在  |
| qqguild:g<guild_id>.guild_admin                 | 服务器管理   | qqguild:g87654321.guild_admin              | 仅当消息来自频道、该用户为服务器管理时存在 |
| qqguild:guild_admin                             | 服务器管理   |                                            | 仅当消息来自频道、该用户为服务器管理时存在 |
| qqguild:g<guild_id>:c<channel_id>.channel_admin | 频道管理    | qqguild:g87654321:c123454321.channel_admin | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:c<channel_id>.channel_admin             | 频道管理    | qqguild:c123454321.channel_admin           | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:g<guild_id>.channel_admin               | 频道管理    | qqguild:g87654321.channel_admin            | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:channel_admin                           | 频道管理    |                                            | 仅当消息来自频道、该用户为频道管理时存在  |
| qqguild:g<guild_id>.role_\<rold_id\>            | 服务器身份组  | qqguild:g87654321.role_233                 | 仅当消息来自频道、该用户在该身份组时存在  |
| qqguild:g<guild_id>:c<channel_id>               | 服务器频道   | qqguild:g87654321:c123454321               | 仅当消息来自频道时存在           |
| qqguild:c<channel_id>                           | 频道      | qqguild:c123454321                         | 仅当消息来自频道时存在           |
| qqguild:g<guild_id>                             | 服务器     | qqguild:g87654321                          | 仅当消息来自频道时存在           |
| qqguild:private                                 | 私聊消息    |                                            | 仅当消息来自私聊时存在           |
| qqguild:channel                                 | 频道消息    |                                            | 仅当消息来自频道时存在           |
| qqguild                                         | 某个平台用户  |                                            |                       |
| all                                             | 所有用户    |                                            |                       |
