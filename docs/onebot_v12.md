nonebot-plugin-access-control for OneBot V12
========

## 主体定义（单级群组）

从上往下优先级从高到低

| 主体                                | 含义             | 示例                        | 必定存在           |
|-----------------------------------|----------------|---------------------------|----------------|
| \<platform>:g<group_id>:<user_id> | 群用户            | qq:g87654321:12345678     | 是              |
| onebot:g<group_id>:<user_id>      | 群用户            | onebot:g87654321:12345678 | 是              |
| \<platform>:<user_id>             | 用户             | qq:12345678               | 是              |
| onebot:<user_id>                  | 用户             | onebot:12345678           | 是              |
| superuser                         | 超级用户           |                           | 仅当该用户为超级用户时存在  |
| \<platform>:g<group_id>           | 群组             | qq:g87654321              | 仅当消息来自群组/频道时存在 |
| onebot:g<group_id>                | 群组             | onebot:g87654321          | 仅当消息来自群组/频道时存在 |
| \<platform>:private               | 私聊消息           | qq:private                | 仅当消息来自私聊时存在    |
| onebot:private                    | 私聊消息（与上一条含义相同） |                           | 仅当消息来自私聊时存在    |
| \<platform>:group                 | 群聊消息           | qq:group                  | 仅当消息来自群聊时存在    |
| onebot:group                      | 群聊消息（与上一条含义相同） |                           | 仅当消息来自群聊时存在    |
| \<platform>                       | 某个平台用户         | qq                        | 是              |
| onebot                            | OneBot用户       |                           | 是              |
| all                               | 所有用户           |                           | 是              |

## 主体定义（两级群组）

从上往下优先级从高到低

| 主体                                              | 含义             | 示例                                     | 必定存在          |
|-------------------------------------------------|----------------|----------------------------------------|---------------|
| \<platform>:g<guild_id>:c<channel_id>:<user_id> | 服务器频道用户        | telegram:g87654321:c123454321:12345678 | 仅当消息来自频道时存在   |
| onebot:g<guild_id>:c<channel_id>:<user_id>      | 服务器频道用户        | onebot:g87654321:c123454321:12345678   | 仅当消息来自频道时存在   |
| \<platform>:c<channel_id>:<user_id>             | 频道用户           | telegram:c123454321:12345678           | 仅当消息来自频道时存在   |
| onebot:c<channel_id>:<user_id>                  | 频道用户           | onebot:c123454321:12345678             | 仅当消息来自频道时存在   |
| \<platform>:g<guild_id>:<user_id>               | 服务器用户          | telegram:g87654321:12345678            | 仅当消息来自服务器时存在  |
| onebot:g<guild_id>:<user_id>                    | 服务器用户          | onebot:g87654321:12345678              | 仅当消息来自服务器时存在  |
| \<platform>:<user_id>                           | 用户             | telegram:12345678                      | 是             |
| onebot:<user_id>                                | 用户             | onebot:12345678                        | 是             |
| superuser                                       | 超级用户           |                                        | 仅当该用户为超级用户时存在 |
| \<platform>:g<guild_id>:c<channel_id>           | 服务器频道          | telegram:g87654321:c123454321          | 仅当消息来自频道时存在   |
| onebot:g<guild_id>:c<channel_id>                | 服务器频道          | onebot:g87654321:c123454321            | 仅当消息来自频道时存在   |
| \<platform>:c<channel_id>                       | 频道             | telegram:c123454321                    | 仅当消息来自频道时存在   |
| onebot:c<channel_id>                            | 频道             | onebot:c123454321                      | 仅当消息来自频道时存在   |
| \<platform>:g<guild_id>                         | 服务器            | telegram:g87654321                     | 仅当消息来自频道时存在   |
| onebot:g<guild_id>                              | 服务器            | onebot:g87654321                       | 仅当消息来自频道时存在   |
| \<platform>:private                             | 私聊消息           | qq:private                             | 仅当消息来自私聊时存在   |
| onebot:private                                  | 私聊消息（与上一条含义相同） |                                        | 仅当消息来自私聊时存在   |
| \<platform>:channel                             | 频道消息           | telegram:channel                       | 仅当消息来自频道时存在   |
| onebot:channel                                  | 频道消息（与上一条含义相同） |                                        | 仅当消息来自频道时存在   |
| \<platform>                                     | 某个平台用户         | qq                                     | 是             |
| onebot                                          | OneBot用户       |                                        | 是             |
| all                                             | 所有用户           |                                        | 是             |
