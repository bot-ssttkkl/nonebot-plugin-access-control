<!-- markdownlint-disable MD033 MD036 MD041 -->

<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

nonebot-plugin-access-control
============

_✨ Nonebot 权限控制 ✨_

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

- [x] 支持**功能级别**的细粒度权限控制
- [x] 对未适配插件也支持**插件级别**的权限控制
- [ ] 支持对权限开关等事件进行监听

## 使用

### 主体

#### 概念

让我们从一个例子引入：QQ上群组G的用户U发送了一条消息，该用户同时具有“用户U”、“群组G成员”、“QQ用户”、“Bot用户”这几个身份。同时QQ上群组G的用户V也发送了一条消息，该用户该用户同时具有“用户V”、“群组G成员”、“QQ用户”、“Bot用户”这几个身份。

如果我们希望对用户进行权限控制，我们可以直接针对“用户U”、“用户V”这个级别分别配置权限。但我们希望对群组进行权限控制时，对群组内的每一个用户都分别配置权限，就有点力不从心了。我们希望能够直接针对“群组G”这个级别进行配置，而无需关心群组内都有什么成员。

我们定义**主体（Subject）为用户所具有的身份，也是设置权限的基本单位。**

一个用户通常拥有多个主体。回到上面的例子，第一位用户拥有“用户U”、“群组G成员”、“QQ用户”、“Bot用户”这四个主体；第二位用户拥有“用户V”、“群组G成员”、“QQ用户”、“Bot用户”这四个主体。用户拥有的所有主体，按照规模从小到大排序，呈现如下图的逐层包含关系：

![](docs/img/1.svg)

当设置权限时，我们直接针对一个主体进行设置。当鉴权时，我们对用户的所有主体按规模从小到大的顺序（下文将此顺序称为优先级顺序），逐一检查是否设置了权限。一旦检查到某个主体设置了权限，就以该主体设置的权限作为该用户的权限。

回到上面的例子，假设我们对主体”群组G“禁用服务，但是对主体”用户V“启用服务。则在群组G内的用户U内将无法使用服务，但是则在群组G内的用户V可以使用。

#### 应用

在实际应用中，我们用一个字符串表示主体。并且我们约定，`all`表示所有用户，`<协议名>`表示所有此协议的用户，除此之外的所有主体均以`<协议名>:`开头。

在OneBot协议中，每个用户所拥有的主体如下表所定义：

| 主体                 | 含义       | 示例               | 必定存在             |
|--------------------|----------|------------------|------------------|
| onebot:<user_id>   | 用户ID     | onebot:12345678  | 是                |
| onebot:g<group_id> | 群组ID     | onebot:g87654321 | 仅当消息来自群组或临时会话时存在 |
| onebot             | OneBot用户 | onebot           | 是                |
| all                | 所有用户     | all              | 是                |

目前仅实现了OneBot协议。如果你能帮助我们进行其他协议适配，欢迎提交PR。

### 服务

**服务（Service）为一组能够进行权限控制的功能的集合。** 服务可以拥有子服务，通过树形结构组织服务，统一管理权限。

整个插件就是一个服务（PluginService）。当插件未进行适配时，该插件只具有一个PluginService。

若需要对插件进行适配，则需要从PluginService创建SubService，为插件的Matcher等功能入口应用SubService。（参考下文插件适配章节）

### 指令

进行权限开关的指令为`/ac`，仅超级用户可用。（通过在配置文件中设置`SUPERUSERS`变量可设置超级用户）

- `/ac subject <主体> allow service <服务>`：为主体启用服务
- `/ac subject <主体> deny service <服务>`：为主体禁用服务
- `/ac subject <主体> remove service <服务>`：为主体删除服务权限配置
- `/ac subject <主体> ls service`：列出主体已配置的服务权限
- `/ac service <服务> ls`：列出服务的子服务层级
- `/ac service <服务> ls subject`：列出服务已配置的主体权限

其中`<服务>`的格式如下：

- `<插件名>`：对整个插件进行开关
- `<插件名>.<子服务名>.<子服务名>.....<子服务名>`：对插件内的某个子服务进行开关（需参照下文对插件进行配置）

## 插件适配

完整代码：[src/nonebot_plugin_ac_demo](src/nonebot_plugin_ac_demo)

1. 创建一个名为nonebot_plugin_ac_demo的插件

2. 通过create_plugin_service函数创建一个PluginServic实例（注意参数必须为插件包名）

```python
from nonebot import require

require("nonebot_plugin_ac_demo")

from nonebot_plugin_access_control.service import create_plugin_service

plugin_service = create_plugin_service("nonebot_plugin_ac_demo")
```

3. 通过PluginService.create_subservice创建SubService实例。调用`SubService.patch_matcher()`应用至Matcher

```python
group1 = plugin_service.create_subservice("group1")

a_matcher = on_command('a')
a_service = group1.create_subservice('a')
a_service.patch_matcher(a_matcher)

@a_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("a")

    
b_matcher = on_command('b')
b_service = group1.create_subservice('b')
b_service.patch_matcher(b_matcher)

@b_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("b")

    
c_matcher = on_command('c')
c_service = plugin_service.create_subservice('c')
c_service.patch_matcher(c_matcher)

@c_matcher.handle()
async def _(matcher: Matcher):
    await matcher.send("c")
```

插件服务的结构如下所示：

![](docs/img/2.svg)

4. 通过指令配置服务权限

执行下面的指令后，所有用户将无法调用指令`/a`与`/b`

```
/ac subject all deny service nonebot_plugin_ac_demo.group1
```

执行下面的指令后，用户12345678将无法调用指令`/a`

```
/ac subject onebot:12345678 deny service nonebot_plugin_ac_demo.group1.a
```

执行下面的指令后，群组87654321的所有用户将无法调用除`/c`以外的任何指令

```
/ac subject onebot:g87654321 deny service nonebot_plugin_ac_demo
/ac subject onebot:g87654321 allow service nonebot_plugin_ac_demo.c
```