nonebot-plugin-access-control for OneBot V12
========

## 主体定义（单级群组）

从上往下优先级从高到低

| 主体                                | TAG                 | 含义                 | 示例                        | 存在条件           |
|-----------------------------------|---------------------|--------------------|---------------------------|----------------|
| \<platform>:g<group_id>:<user_id> | platform:group:user | 来自\<platform>的群用户  | qq:g87654321:12345678     | 仅当消息来自群组时存在    |
| onebot:g<group_id>:<user_id>      | onebot:group:user   | 来自OneBot的群用户       | onebot:g87654321:12345678 | 仅当消息来自群组时存在    |
| \<platform>:<user_id>             | platform:user       | 来自\<platform>的用户   | qq:12345678               |                |
| onebot:<user_id>                  | onebot:user         | 来自OneBot的用户        | onebot:12345678           |                |
| superuser                         | superuser           | 超级用户               |                           | 仅当该用户为超级用户时存在  |
| \<platform>:g<group_id>           | platform:group      | 来自\<platform>的群组   | qq:g87654321              | 仅当消息来自群组/频道时存在 |
| onebot:g<group_id>                | onebot:group        | 来自OneBot的群组        | onebot:g87654321          | 仅当消息来自群组/频道时存在 |
| \<platform>:private               | platform:chat_type  | 来自\<platform>的私聊消息 | qq:private                | 仅当消息来自私聊时存在    |
| onebot:private                    | onebot:chat_type    | 来自OneBot的私聊消息      |                           | 仅当消息来自私聊时存在    |
| private                           | chat_type           | 私聊消息               | 仅当消息来自私聊时存在               |                |     |                |                           |                |
| \<platform>:group                 | platform:chat_type  | 来自\<platform>的群聊消息 | qq:group                  | 仅当消息来自群聊时存在    |
| onebot:group                      | onebot:chat_type    | 来自OneBot的私聊消息      |                           | 仅当消息来自群聊时存在    |
| group                             | chat_type           | 私聊消息               |                           | 仅当消息来自私聊时存在    |                |                           |                |
| \<platform>                       | platform            | 来自\<platform>的用户   | qq                        |                |
| onebot                            | onebot              | 来自OneBot的用户        |                           |                |
| all                               | all                 | 所有用户               |                           |                |

## 主体定义（两级群组）

从上往下优先级从高到低

| 主体                                              | TAG                         | 含义                    | 示例                                     | 存在条件          |
|-------------------------------------------------|-----------------------------|-----------------------|----------------------------------------|---------------|
| \<platform>:g<guild_id>:c<channel_id>:<user_id> | platform:guild:channel:user | 来自\<platform>的服务器频道用户 | telegram:g87654321:c123454321:12345678 | 仅当消息来自频道时存在   |
| onebot:g<guild_id>:c<channel_id>:<user_id>      | onebot:guild:channel:user   | 来自OneBot的服务器频道用户      | onebot:g87654321:c123454321:12345678   | 仅当消息来自频道时存在   |
| \<platform>:c<channel_id>:<user_id>             | platform:channel:user       | 来自\<platform>的频道用户    | telegram:c123454321:12345678           | 仅当消息来自频道时存在   |
| onebot:c<channel_id>:<user_id>                  | onebot:channel:user         | 来自OneBot的频道用户         | onebot:c123454321:12345678             | 仅当消息来自频道时存在   |
| \<platform>:g<guild_id>:<user_id>               | platform:guild:user         | 来自\<platform>的服务器用户   | telegram:g87654321:12345678            | 仅当消息来自服务器时存在  |
| onebot:g<guild_id>:<user_id>                    | onebot:guild:user           | 来自OneBot的服务器用户        | onebot:g87654321:12345678              | 仅当消息来自服务器时存在  |
| \<platform>:<user_id>                           | platform:user               | 来自\<platform>的用户      | telegram:12345678                      |               |
| onebot:<user_id>                                | onebot:user                 | 来自OneBot的用户           | onebot:12345678                        |               |
| superuser                                       | superuser                   | 超级用户                  |                                        | 仅当该用户为超级用户时存在 |
| \<platform>:g<guild_id>:c<channel_id>           | platform:guild:channel      | 来自\<platform>的服务器频道   | telegram:g87654321:c123454321          | 仅当消息来自频道时存在   |
| onebot:g<guild_id>:c<channel_id>                | onebot:guild:channel        | 来自OneBot的服务器频道        | onebot:g87654321:c123454321            | 仅当消息来自频道时存在   |
| \<platform>:c<channel_id>                       | platform:channel            | 来自\<platform>的频道      | telegram:c123454321                    | 仅当消息来自频道时存在   |
| onebot:c<channel_id>                            | onebot:channel              | 来自OneBot的频道           | onebot:c123454321                      | 仅当消息来自频道时存在   |
| \<platform>:g<guild_id>                         | platform:guild              | 来自\<platform>的服务器     | telegram:g87654321                     | 仅当消息来自频道时存在   |
| onebot:g<guild_id>                              | onebot:guild                | 来自OneBot的服务器          | onebot:g87654321                       | 仅当消息来自频道时存在   |
| \<platform>:private                             | platform:private            | 来自\<platform>的私聊消息    | qq:private                             | 仅当消息来自私聊时存在   |
| onebot:private                                  | onebot:private              | 来自OneBot的私聊消息         |                                        | 仅当消息来自私聊时存在   |
| private                                         | private                     | 私聊消息                  |                                        | 仅当消息来自私聊时存在   |         
| \<platform>:channel                             | platform:channel            | 来自\<platform>的频道消息    | telegram:channel                       | 仅当消息来自频道时存在   |
| onebot:channel                                  | onebot:channel              | 来自OneBot的频道消息         |                                        | 仅当消息来自频道时存在   |
| channel                                         | channel                     | 频道消息                  |
| \<platform>                                     | platform                    | 来自\<platform>的用户      | qq                                     |               |
| onebot                                          | onebot                      | 来自OneBot的用户           |                                        |               |
| all                                             | all                         | 所有用户                  |                                        |               |
