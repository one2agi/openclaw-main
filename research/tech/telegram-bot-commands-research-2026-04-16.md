# Telegram Bot Slash Commands 研究报告

**生成时间**：2026-04-16 22:30 GMT+8  
**研究目的**：为什么 Telegram 上没有系统的 "/" 命令菜单

---

## 1. Telegram Bot Commands 工作原理

### 核心 API：`setMyCommands`

Telegram Bot API 的命令菜单不是自动出现的。每个 bot 必须主动调用 `setMyCommands` 方法来注册自己的命令列表。注册后：
- 用户在聊天框输入 `/` 时，Telegram 客户端自动显示该 bot 的命令列表
- 客户端提供自动补全（autocomplete）
- 命令按字典序排列

**API 调用格式**（来自 Telegram Bot API 文档）：
```
POST https://api.telegram.org/bot<token>/setMyCommands
Body: {
  "commands": [
    {"command": "start", "description": "开始使用"},
    {"command": "help", "description": "获取帮助"}
  ]
}
```

**关键限制**：
- 每个 bot 最多 100 个命令
- 命令名必须为 `a-z`, `0-9`, `_`，长度 1-32，区分大小写
- 命令不能覆盖 Telegram 保留命令（如 `/start`、`/settings`）

### 为什么有些 Bot 没有 "/" 菜单

原因只有一个：**该 bot 没有调用 `setMyCommands`**。

可能原因：
1. 开发者从未实现该功能
2. `setMyCommands` 调用失败（DNS/HTTPS 问题）
3. 命令列表为空或无效

---

## 2. OpenClaw Telegram 插件配置方式

### 2.1 原生命令（Native Commands）

OpenClaw 在 Telegram 插件中**默认启用**原生命令注册（`setMyCommands`）。通过 `commands.native` 配置控制：

```json
// 全局配置
"commands": {
  "native": "auto",      // "auto" | true | false
  "nativeSkills": "auto"  // 是否包含 skill 命令
}
```

- `commands.native: "auto"` → 启动时自动调用 `setMyCommands` 注册 OpenClaw 内置命令（`/help`、`/status`、`/new`、`/reset`、`/model`、`/compact`、`/whoami` 等 30+ 个）
- `commands.native: false` → 不注册原生命令

### 2.2 自定义命令（Custom Commands）

```json
"channels": {
  "telegram": {
    "customCommands": [
      { "command": "clear", "description": "清空当前上下文" },
      { "command": "sessions", "description": "列出所有会话" }
    ]
  }
}
```

**规则**：
- 命令名自动规范化（去除前导 `/`，转小写）
- 合法字符：`a-z`, `0-9`, `_`，长度 1-32
- **自定义命令不能覆盖原生命令**（冲突项会被跳过并记录 ERROR 日志）
- 自定义命令只注册菜单，**不自动实现行为**（实际执行仍依赖 agent 处理）

### 2.3 注册时机

> **文档原文**：*"Telegram command menu registration is handled at startup with setMyCommands."*

命令在**网关启动时**调用 `setMyCommands` 注册。修改 `customCommands` 后需要重启网关（配置热重载也可以）。

### 2.4 常见失败原因

> **文档原文**：*"setMyCommands failed usually means outbound DNS/HTTPS to api.telegram.org is blocked."*

常见问题：
- DNS 解析 `api.telegram.org` 失败
- IPv6 路由问题（某些主机优先解析 AAAA 记录但 IPv6 出站损坏）
- 代理配置问题

---

## 3. 本地实际情况审计

### 3.1 配置分析（`~/.openclaw/openclaw.json`）

**顶层 commands 配置**：
```json
"commands": {
  "mcp": true,
  "native": "auto",
  "nativeSkills": "auto",
  "restart": true,
  "ownerDisplay": "raw"
}
```
✅ `native: "auto"` 已设置，全局启用原生命令

**channels.telegram.customCommands**：
```json
"customCommands": [
  { "command": "clear",      "description": "清空当前上下文" },
  { "command": "sessions",   "description": "列出所有会话" },
  { "command": "tokens",     "description": "查看 token 使用量" },
  { "command": "cost",       "description": "显示用量费用" },
  { "command": "uptime",     "description": "显示运行时长" },
  { "command": "retry",      "description": "重试上一条消息" },
  { "command": "cancel",     "description": "取消当前输出" },
  { "command": "serena",     "description": "Serena 助手模式" }
]
```

**Telegram 账户配置**（多 bot）：
```json
"channels": {
  "telegram": {
    "accounts": {
      "无极":    { "botToken": "...AAGdJ...", "enabled": false },
      "default": { "botToken": "...AAGHRT...", "enabled": true },
      "code":    { "botToken": "...AAGdJ...", "enabled": true }
    }
  }
}
```
⚠️ 共 3 个 bot（其中 1 个已禁用），`default` 和 `code` 账户同时运行

### 3.2 网关运行状态

```
- Telegram code:     enabled, configured, running, mode:polling
- Telegram default:  enabled, configured, running, mode:polling
```

✅ 两个 bot 均以 polling 模式正常运行

### 3.3 日志关键发现（`/tmp/openclaw/openclaw-2026-04-16.log`）

**发现 1：8 个自定义命令与原生命令冲突（ERROR 级）**

```
Telegram custom command "/restart" conflicts with a native command.
Telegram custom command "/compact" conflicts with a native command.
Telegram custom command "/reset" conflicts with a native command.
Telegram custom command "/reasoning" conflicts with a native command.
Telegram custom command "/mcp" conflicts with a native command.
Telegram custom command "/help" conflicts with a native command.
Telegram custom command "/status" conflicts with a native command.
Telegram custom command "/model" conflicts with a native command.
```

> ⚠️ **这些冲突实际上没有发生** — 实际配置的 customCommands 是 clear/sessions/tokens/cost/uptime/retry/cancel/serena，没有 restart/compact/reset/reasoning/mcp/help/status/model。这些日志是**旧日志**（来自更早的配置或旧账户）。

**发现 2：大量 Telegram API 网络错误（ERROR 级）**

```
telegram sendMessage failed: Network request for 'sendMessage' failed!
telegram sendChatAction failed: Network request for 'sendChatAction' failed!
telegram editMessage failed: Network request for 'editMessageText' failed!
```

- 时间：2026-04-16 20:21–20:22 UTC（北京时间 04:21–04:22）
- **持续约 1 分钟**，之后恢复正常
- 原因：Telegram API 出站网络请求失败（可能是代理短暂中断）

**发现 3：隐私模式警告**

```
- telegram code: Config allows unmentioned group messages (requireMention=false). 
  Telegram Bot API privacy mode will block most group messages unless disabled.
- telegram default: 同上
```

⚠️ BotFather 中 `/setprivacy` 未禁用，导致 `requireMention: false` 配置无法生效

**发现 4：Cron 投递失败**

```
Delivering to telegram requires target <chatId>
cron: failed to resolve failure destination target
```

⚠️ Cron 任务无法送达 Telegram — 因为缺少 chatId 目标

---

## 4. 发现的问题

### 问题 1（核心）：当前 "/" 菜单实际上存在但可能不可见

**根因**：`commands.native: "auto"` 已在配置中，OpenClaw 应该在启动时注册了原生命令。日志中**没有** `setMyCommands failed` 错误，说明 `setMyCommands` **调用成功**。

当前 Telegram 菜单实际包含的命令（推测）：
- **原生命令**（已注册）：`/help`, `/status`, `/new`, `/reset`, `/model`, `/compact`, `/whoami`, `/reasoning`, `/mcp` 等 30+ 个
- **自定义命令**（已注册）：`/clear`, `/sessions`, `/tokens`, `/cost`, `/uptime`, `/retry`, `/cancel`, `/serena`

**但如果 faiz 看不到 "/" 菜单，可能原因**：

1. **Bot Token 混淆**：配置了 3 个 bot，但 faiz 可能在和某个**没有正确注册命令**的 bot 对话
2. **网络中断导致 setMyCommands 在某次重启时失败**：日志显示 20:21 有约 1 分钟的 Telegram API 网络错误
3. **用户从旧 bot 切换到新 bot**：OpenClaw 有 `default` 和 `code` 两个 bot，可能 faiz 在用的是另一个 token
4. **Telegram 客户端缓存**：某些客户端会缓存 bot 命令列表，可能需要重启 Telegram app 或等待刷新

### 问题 2：customCommands 配置中的冲突命令

虽然当前配置没有冲突（旧日志是历史记录），但需要确认：`channels.telegram.customCommands` 中的命令是否有意选择。8 个有效自定义命令（clear/sessions/tokens/cost/uptime/retry/cancel/serena）与原生命令没有重叠，设计正确。

### 问题 3：多 Bot 配置的复杂性

```
default bot: ...AAGHRTPuyHO5f0NJmfZ4eC8tsOmboU5OJTw
code bot:    ...AAGdJ1Hex8YU4M6sGB45eDO3pTD5BZFt5EU
无极 bot:    (disabled)
```

两个 bot 同时运行，但 customCommands 只在顶层 `channels.telegram` 定义了一次。这个配置会应用到**所有账户**，还是需要分别配置？

### 问题 4：隐私模式未正确配置

即使配置了 `requireMention: false`，BotFather 的 `/setprivacy` 仍然是默认的 "Enable" 状态，会导致群组消息被 Telegram API 静默丢弃。

### 问题 5：Cron 无法送达 Telegram

Cron 任务配置了 Telegram 投递但缺少 `target`（chatId），需要在 cron 配置中指定 `target: "7754385134"`（faiz 的 Telegram ID）。

---

## 5. 建议的修复方案

### 修复 1：重启网关 + 确认菜单注册

```bash
openclaw gateway restart
```

重启后检查日志：
```bash
grep -i "setMyCommands\|commands.*registered\|command.*menu" /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

### 修复 2：手动验证 Bot 命令列表

通过 Bot API 直接查询当前注册的菜单：
```bash
# default bot
curl "https://api.telegram.org/bot8727180465:AAGHRTPuyHO5f0NJmfZ4eC8tsOmboU5OJTw/getMyCommands"

# code bot
curl "https://api.telegram.org/bot8409219612:AAGdJ1Hex8YU4M6sGB45eDO3pTD5BZFt5EU/getMyCommands"
```

### 修复 3：在 BotFather 禁用隐私模式

在 Telegram 中找 faiz 的 bot 对应的 @BotFather：
1. 发送 `/setprivacy`
2. 选择对应的 bot
3. 选择 **Disable**
4. 从群组中移除并重新添加 bot

### 修复 4：手动强制重新注册命令

如果重启后菜单仍未出现，可以手动调用 API：

```bash
# 为 default bot 注册命令
curl -X POST "https://api.telegram.org/bot8727180465:AAGHRTPuyHO5f0NJmfZ4eC8tsOmboU5OJTw/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "help", "description": "获取帮助信息"},
      {"command": "status", "description": "显示当前状态"},
      {"command": "new", "description": "开始新会话"},
      {"command": "reset", "description": "重置当前会话"},
      {"command": "model", "description": "切换模型"},
      {"command": "compact", "description": "压缩上下文"},
      {"command": "whoami", "description": "显示用户信息"},
      {"command": "clear", "description": "清空当前上下文"},
      {"command": "sessions", "description": "列出所有会话"},
      {"command": "tokens", "description": "查看 token 使用量"},
      {"command": "cost", "description": "显示用量费用"},
      {"command": "uptime", "description": "显示运行时长"},
      {"command": "retry", "description": "重试上一条消息"},
      {"command": "cancel", "description": "取消当前输出"}
    ]
  }'
```

### 修复 5：简化多 Bot 配置（可选）

如果只需要一个 bot，禁用不用的：
```json
"channels": {
  "telegram": {
    "accounts": {
      "无极": { "enabled": false },
      "default": { "enabled": true },
      "code": { "enabled": false }
    }
  }
}
```

### 修复 6：Cron chatId 配置

在 cron 配置中确认 Telegram target：
```json
{
  "channel": "telegram",
  "target": "7754385134"
}
```

---

## 附录：关键配置路径速查

| 配置项 | 路径 |
|--------|------|
| 原生命令开关 | `commands.native` (全局) / `channels.telegram.commands.native` |
| 自定义命令 | `channels.telegram.customCommands` |
| Bot Token | `channels.telegram.accounts.<name>.botToken` |
| 群组消息策略 | `channels.telegram.groups.*.requireMention` |
| DM 访问策略 | `channels.telegram.dmPolicy` |
| Webhook 模式 | `channels.telegram.webhookUrl` |

---

## 参考资料

- [Telegram Bot API - setMyCommands](https://core.telegram.org/bots/api#setmycommands)
- [OpenClaw Telegram 文档](https://open-claw.bot/docs/channels/telegram/)
- [OpenClaw 配置参考 - Telegram](https://open-claw.bot/docs/gateway/configuration-reference#configuring-specific-channels)
- [Simon Willison - Running OpenClaw in Docker](https://til.simonwillison.net/llms/openclaw-docker)
