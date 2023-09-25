nonebot-plugin-access-control for OneBot V11
========

## 主体定义

从上往下优先级从高到低

| 主体                           | TAG                  | 含义            | 示例                        | 存在条件          |
|------------------------------|----------------------|---------------|---------------------------|---------------|
| qq:g<group_id>:<user_id>     | platform:group:user  | 来自QQ的群用户      | qq:g87654321:12345678     | 仅当消息来自群组时存在   |
| onebot:g<group_id>:<user_id> | onebot:group:user    | 来自OneBot的群用户  | onebot:g87654321:12345678 | 仅当消息来自群组时存在   |
| qq:<user_id>                 | platform:user        | 来自QQ的用户       | qq:12345678               |               |
| onebot:<user_id>             | onebot:user          | 来自OneBot的用户   | onebot:12345678           |               |
| superuser                    | superuser            | 超级用户          |                           | 仅当该用户为超级用户时存在 |
| qq:g<group_id>.group_owner   | qq:group.group_owner | 群主            | qq.g87654321.group_owner  | 仅当消息来自群组时存在   |
| qq:group_owner               | qq:group_owner       | 群主            |                           | 仅当消息来自群组时存在   |
| qq:g<group_id>.group_admin   | qq:group.group_admin | 群管理           | qq.g87654321.group_admin  | 仅当消息来自群组时存在   |
| qq:group_admin               | qq:group_admin       | 群管理           |                           | 仅当消息来自群组时存在   |
| qq:g<group_id>               | platform:group       | 来自QQ的群组       | qq:g87654321              | 仅当消息来自群组时存在   |
| onebot:g<group_id>           | onebot:group         | 来自OneBot的群组   | onebot:g87654321          | 仅当消息来自群组时存在   |
| qq:private                   | platform:chat_type   | 来自QQ的私聊消息     |                           | 仅当消息来自私聊时存在   |
| onebot:private               | onebot:chat_type     | 来自OneBot的私聊消息 |                           | 仅当消息来自私聊时存在   |
| private                      | chat_type            | 私聊消息          |                           | 仅当消息来自私聊时存在   |
| qq:group                     | platform:chat_type   | 来自QQ的群聊消息     |                           | 仅当消息来自群聊时存在   |
| onebot:group                 | onebot:chat_type     | 来自OneBot的群聊消息 |                           | 仅当消息来自群聊时存在   |
| group                        | group                | 群聊消息          |                           | 仅当消息来自群聊时存在   |
| qq                           | platform             | 来自QQ的用户       |                           |               |
| onebot                       | onebot               | 来自OneBot的用户   |                           |               |
| all                          | all                  | 所有用户          |                           |               |
