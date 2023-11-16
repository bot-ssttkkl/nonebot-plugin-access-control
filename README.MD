<!-- markdownlint-disable MD033 MD036 MD041 -->

<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

nonebot-plugin-access-control
============

_✨ Nonebot 权限控制插件 ✨_

</div>


<p align="center">
  <a href="https://raw.githubusercontent.com/ssttkkl/nonebot-plugin-access-control/master/LICENSE">
    <img src="https://img.shields.io/github/license/ssttkkl/nonebot-plugin-access-control.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-access-control">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-access-control.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
</p>

## 特点

- 功能
    - [x] 支持针对用户/群组的权限开关
    - [x] 支持限制同一用户在一定时间内的指令调用次数
    - [x] 对未适配插件提供**插件级别**的控制支持
- 插件适配
    - [x] 支持**功能级别**的细粒度控制
    - [x] 支持对权限开关等事件进行订阅
- 拓展
    - [x] 支持开发者拓展定义新的主体
- CLI插件
    - [x] 支持通过控制台中执行`nb accctrl`进入权限控制台

## 使用

### 主体

#### 概念

当我们对用户进行权限控制时，我们想要的是针对拥有某种同样身份的所有用户进行配置，而不是对每一个具体用户分别配置。因此，我们引入主体的概念。
**主体（Subject）代表了拥有某种同样身份的用户的集合，也是设置权限的基本单位。**
当我们说用户具有某个主体，也就是说用户在该主体所代表的集合内。换句话说，主体就是一个用户所具有的身份。

一个用户通常拥有多个主体。举个例子：QQ上群组G的用户U发送了一条消息，该用户同时具有“用户U”、“群组G成员”、“QQ用户”、“Bot用户”这几个主体。同时QQ上群组G的用户V也发送了一条消息，该用户该用户同时具有“用户V”、“群组G成员”、“QQ用户”、“Bot用户”这几个主体。

当设置权限时，我们直接针对一个主体进行设置。当鉴权时，我们对用户的所有主体**按优先级从高到低的顺序**
，逐一检查是否设置了权限。一旦检查到某个主体设置了权限，就以该主体设置的权限作为该用户的权限。

回到上面的例子，假设我们对主体”群组G“禁用服务，但是对主体”用户V“启用服务。则用户U在群组G内将无法使用服务，但是用户V在群组G内可以使用。

在插件使用中，我们用一个字符串表示主体，例如`qq:12345678`表示QQ用户12345678、`qq:g87654321`表示QQ群组87654321。

我们约定：`all`表示所有用户、`superuser`表示超级用户、`<平台名>`表示所有此平台的用户、`<协议名>`
表示所有此协议的用户、所有与平台相关的主体均以`<平台名>:`开头、所有与协议相关的主体均以`<协议名>:`开头。

插件依赖[nonebot-plugin-session](https://github.com/noneplugin/nonebot-plugin-session)提取事件的主体，各适配器的主体定义如下：

- [OneBot V11](docs/onebot_v11.md)
- [OneBot V12](docs/onebot_v12.md)
- [Kaiheila](docs/kaiheila.md)
- [QQ Guild](docs/qqguild.md)
- Telegram：未测试，参考OneBot V12的定义

### 服务

**服务（Service）为一组能够进行权限控制的功能的集合。** 服务可以拥有子服务，通过树形结构组织服务，统一管理权限。

整个NoneBot是一个名为nonebot的服务，为树形结构的根节点，其直接子节点为所有插件。

一个插件是一个服务（PluginService），其父节点为nonebot。当插件未进行适配时，该插件只具有这一个PluginService。对插件进行适配，则需要从插件的PluginService创建SubService，为插件的Matcher等功能入口应用SubService。（参考下文插件适配章节）

（为防止意外发生，nonebot_plugin_access_control本身不可以进行权限开关）

当某主体需要检查某服务是否可用时，将从该服务开始检查是否为该主体配置了权限，若未配置则检查其父服务，以此类推直到检查到根节点nonebot。

换句话说，当鉴权时，我们逐一对用户的所有主体**按优先级从高到低的顺序**，**按服务的节点深度从深到浅的顺序**
检查该服务及其所有祖先节点配置的权限。因此，在节点深度较浅的服务配置的高优先级的主体配置，也会覆盖在节点深度较深的服务配置的低优先级的主体配置。

通过指令可查看所有服务及子服务层级：

- `/ac service ls`：列出所有服务与子服务层级
- `/ac service ls --srv <服务>`：列出服务的子服务层级

其中`<服务>`的格式如下：

- `nonebot`：对整个NoneBot进行开关
- `<插件名>`：对整个插件进行开关
- `<插件名>.<子服务名>.<子服务名>.....<子服务名>`：对插件内的某个子服务进行开关（需参照下文对插件进行配置）

### 鉴权

通过指令可实现权限开关：

- `/ac permission allow --sbj <主体> --srv <服务>`：为主体启用服务
- `/ac permission deny --sbj <主体> --srv <服务>`：为主体禁用服务
- `/ac permission rm --sbj <主体> --srv <服务>`：为主体删除服务权限配置
- `/ac permission ls`：列出所有已配置的权限
- `/ac permission ls --sbj <主体>`：列出主体已配置的服务权限
- `/ac permission ls --srv <服务>`：列出服务已配置的主体权限
- `/ac permission ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的权限

其中`<服务>`的格式同上

### 限流

插件还提供了限流的功能（限制同一用户在一定时间内的指令调用次数）。

限流规则同样是针对服务及主体的。与鉴权不同的是，限流规则是串联的。应用在一个用户拥有的所有主体的限流规则，与应用在一个服务及其所有祖先服务的限流规则，会同时对用户产生限制。

举个例子，如果我们设置了”主体`all`每天最多调用100次`nonebot`服务“，”主体`qq:g87654321`
每分钟最多调用5次`nonebot_plugin_pixivbot`服务“。一位拥有`qq:12345678`、`qq:g87654321`、`qq`、`all`
这四个主体的用户尝试调用`nonebot_plugin_pixivbot.xxx`服务时，将同时受到以上两条规则的限制。

如果我不希望这样的串联，该怎么办？通过为规则设置”覆写“属性，可以覆盖掉所有优先级低于该规则的规则。规则的优先级比较规则如下：

- 若主体优先级不一致，按照主体优先级
- 否则，按照服务的父子关系，父服务优先级低于子服务

通过指令可对限流规则进行操作：

- `/ac limit add --sbj <主体> --srv <服务> --limit <次数> --span <时间间隔> [--overwrite]`
  ：为主体与服务添加限流规则（`--overwrite`：为规则设置”覆写“属性）
- `/ac limit rm <规则ID>`：删除限流规则
- `/ac limit ls`：列出所有已配置的限流规则
- `/ac limit ls --sbj <主体>`：列出主体已配置的限流规则
- `/ac limit ls --srv <服务>`：列出服务已配置的限流规则
- `/ac limit ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的限流规则
- `/ac limit reset`：重置限流计数

其中`<服务>`的格式同上

### 指令一览

进行控制的指令为`/ac`，仅超级用户可用。（通过在配置文件中设置`SUPERUSERS`变量可设置超级用户）

（注意：0.3.0版本对指令进行了一次大的更改）

- 帮助
    - `/ac help`：显示此帮助
- 权限控制
    - `/ac permission allow --sbj <主体> --srv <服务>`：为主体启用服务
    - `/ac permission deny --sbj <主体> --srv <服务>`：为主体禁用服务
    - `/ac permission rm --sbj <主体> --srv <服务>`：为主体删除服务权限配置
    - `/ac permission ls`：列出所有已配置的权限
    - `/ac permission ls --sbj <主体>`：列出主体已配置的服务权限
    - `/ac permission ls --srv <服务>`：列出服务已配置的主体权限
    - `/ac permission ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的权限
- 流量限制
    - `/ac limit add --sbj <主体> --srv <服务> --limit <次数> --span <时间间隔> [--overwrite]`：为主体与服务添加限流规则
    - `/ac limit rm <规则ID>`：删除限流规则
    - `/ac limit ls`：列出所有已配置的限流规则
    - `/ac limit ls --sbj <主体>`：列出主体已配置的限流规则
    - `/ac limit ls --srv <服务>`：列出服务已配置的限流规则
    - `/ac limit ls --sbj <主体> --srv <服务>`：列出主体与服务已配置的限流规则
    - `/ac limit reset`：重置限流计数
- 服务查看
    - `/ac service ls`：列出所有服务与子服务层级
    - `/ac service ls --srv <服务>`：列出服务的子服务层级
- 主体测试
    - `/ac subject`：列出消息发送者的所有主体

其中`<服务>`的格式如下：

- `nonebot`：对整个NoneBot进行开关
- `<插件名>`：对整个插件进行开关
- `<插件名>.<子服务名>.<子服务名>.....<子服务名>`：对插件内的某个子服务进行开关（需参照下文对插件进行配置）

### 示例

首先编辑配置文件，打开对未适配插件的支持：

```
ACCESS_CONTROL_AUTO_PATCH_ENABLED=true
```

假设bot加载了内置插件echo

```python
nonebot.load_builtin_plugins("echo")
```

#### 鉴权

执行下面的指令后，QQ用户12345678将无法调用指令`/echo`

```
/ac permission deny --sbj qq:12345678 --srv echo
```

执行下面的指令后，QQ用户12345678将无法调用所有指令

```
/ac permission deny --sbj all --srv nonebot
```

执行下面的指令后，QQ群组87654321的所有用户（QQ用户12345678除外）将无法调用指令`/echo`

```
/ac permission allow --sbj qq:12345678 --srv echo
/ac permission deny --sbj qq:g87654321 --srv echo
```

执行下面的指令后，所有用户将无法调用指令`/echo`

```
/ac permission deny --sbj all --srv echo
```

#### 限流

执行下面的指令后，所有用户每天只能调用100次任意指令，且每分钟只能调用三次指令`/echo`

```
/ac limit add --sbj all --srv nonebot --span 1d --limit 100
/ac limit add --sbj all --srv echo --span 1m --limit 3
```

执行下面的指令后，QQ群组87654321的所有用户（QQ用户12345678除外）每分钟只能调用三次指令`/echo`

（QQ用户12345678每分钟能够调用114514次指令`/echo`）

```
/ac limit add --sbj qq:g87654321 --srv echo --span 1m --limit 3
/ac limit add --sbj qq:12345678 --srv echo --span 1m --limit 114514 --overwrite
```

## 插件适配

参考 [https://github.com/ssttkkl/nonebot-plugin-access-control-api/blob/v1.1.0/README.MD]

## CLI支持

可以通过控制台中执行`nb accctrl`进入权限控制台，使用方式与`/ac`指令类似。

## 配置项

### 数据库配置

参考 https://github.com/nonebot/plugin-orm#%E9%85%8D%E7%BD%AE%E9%A1%B9

### access_control_default_permission

未设置权限时的默认行为

可选值：`allow`, `deny`

默认值：`allow`

### access_control_auto_patch_enabled

是否启用对未适配插件的权限控制

类型：`bool`

默认值：`False`

### access_control_auto_patch_ignore

对指定的未适配插件将不启用权限控制

类型：`List[str]`

默认值：`[]`

### access_control_reply_on_permission_denied_enabled

因无权限而拒绝执行时，是否向用户回复消息

类型：`bool`

默认值：`False`

### access_control_reply_on_permission_denied

因无权限而拒绝执行时向用户回复的消息

类型：`str`

默认值：`"你没有权限执行该指令"`

### access_control_reply_on_rate_limited_enabled

因到达最大次数而拒绝执行时，是否向用户回复消息

类型：`bool`

默认值：`False`

### access_control_reply_on_rate_limited

因到达最大次数而拒绝执行时向用户回复的消息

类型：`str`

### access_control_rate_limit_token_storage

限流计数使用的存储方式，支持内存存储（inmemory）与数据库存储（datastore）。

内存存储会在重启后重置限流计数，数据库存储则不会。同时数据库存储还能够实现多个NoneBot实例共享限流计数，适用于分布式Bot应用。

在性能上，内存存储优于数据库存储。默认使用的是内存存储。

可选值：`inmemory`, `datastore`

默认值：`inmemory`

## Q&A

### **本插件与[nonebot_plugin_rauthman](https://github.com/Lancercmd/nonebot_plugin_rauthman)

和[nonebot-plugin-manager](https://github.com/nonepkg/nonebot-plugin-manager)等其他权限管理插件有什么差别？**

[nonebot_plugin_rauthman](https://github.com/Lancercmd/nonebot_plugin_rauthman)
支持功能级别的细粒度权限控制，但是需要插件进行适配，对于未适配插件不起作用。[nonebot-plugin-manager](https://github.com/nonepkg/nonebot-plugin-manager)
则实现了非侵入式的权限控制。

本插件主要受这两个插件的启发，结合了这两个插件的优点。既支持非侵入式应用到原有插件，也支持对插件进行适配以获得更多feature。同时提供事件订阅机制，以便插件开发者更灵活处理权限。

同时，上述两款插件均只支持OneBot V11协议，而本插件设计之初就考虑到了除OneBot V11以外的协议，具有更强的可扩展性。

## 在线乞讨

<details><summary>点击请我打两把maimai</summary>

![](https://github.com/ssttkkl/ssttkkl/blob/main/afdian-ssttkkl.jfif)

</details>

## LICENSE

> MIT License
>
> Copyright (c) 2022 ssttkkl
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
> 
