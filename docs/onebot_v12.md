nonebot-plugin-access-control for OneBot V12
========

## 主体定义

从上往下优先级从高到低

| 主体                      | 含义       | 示例                 | 必定存在           |
|-------------------------|----------|--------------------|----------------|
| \<platform>:<user_id>   | 用户       | qq:12345678        | 是              |
| onebot:<user_id>        | 用户       | onebot:12345678    | 是              |
| superuser               | 超级用户     |                    | 仅当该用户为超级用户时存在  |
| \<platform>:c<group_id> | 频道       | telegram:g87654321 | 仅当消息来自频道时存在    |
| onebot:c<group_id>      | 频道       | onebot:g87654321   | 仅当消息来自频道时存在    |
| \<platform>:g<group_id> | 群组/服务器   | qq:g87654321       | 仅当消息来自群组/频道时存在 |
| onebot:g<group_id>      | 群组/服务器   | onebot:g87654321   | 仅当消息来自群组/频道时存在 |
| \<platform>             | 某个平台用户   | qq                 | 是              |
| onebot                  | OneBot用户 |                    | 是              |
| all                     | 所有用户     |                    | 是              |
