---
name: openclaw-md-guide
description: OpenClaw 工作区文档机制指南。当需要理解 OpenClaw 的 Bootstrap 文件体系、Context Injection、记忆管理时使用。
---

# OpenClaw Markdown 文档机制指南

> 整理：2026-04-21 | 来源：系统调研

---

## 一、两种文档体系

| 体系            | 文件                                                                 | 注入方式            |
| ------------- | ------------------------------------------------------------------ | --------------- |
| **Bootstrap** | AGENTS.md / SOUL.md / TOOLS.md / IDENTITY.md / USER.md / MEMORY.md | 每次 session 固定注入 |
| **Skills**    | `skills/<name>/SKILL.md`                                           | 按需读取（on-demand） |

---

## 二、Bootstrap 文件详解

| 文件                       | 定位       | 职责                      |
| ------------------------ | -------- | ----------------------- |
| **AGENTS.md**            | 操作手册（宪法） | 启动流程、行为守则、工具使用原则、记忆管理策略 |
| **SOUL.md**              | 个性与声音    | 语气、价值观、决策风格、角色定位        |
| **TOOLS.md**             | 本地工具笔记   | 环境配置、设备别名、偏好设置          |
| **IDENTITY.md**          | 身份卡      | Agent 名称、emoji、简短自我介绍   |
| **USER.md**              | 用户画像     | 用户偏好、称呼、背景信息            |
| **MEMORY.md**            | 长期记忆     | 持久事实、历史决策、经验总结          |
| **memory/YYYY-MM-DD.md** | 每日日志     | 当天运行上下文、观察记录            |
| **HEARTBEAT.md**         | 心跳任务模板   | 定时/后台任务的指令模板            |

### 注入规则

- AGENTS.md / SOUL.md / TOOLS.md / IDENTITY.md / USER.md：**每次 session 必注**
- MEMORY.md：**仅主会话（DM）注入**，群聊/子 Agent 不注入（防泄露）
- memory/YYYY-MM-DD.md：**按需读取**，非自动全注

### 截断机制

所有文件受 `bootstrapMaxChars`（单文件上限）和 `bootstrapTotalMaxChars`（总上限）限制，超出自动截断并插入警告。

---

## 三、Skills 机制

| 项目     | 说明                                             |
| ------ | ---------------------------------------------- |
| 位置     | `~/.openclaw/workspace/skills/<name>/SKILL.md` |
| 元数据注入  | 名称 + 描述固定注入系统提示                                |
| 完整内容注入 | 按需读取（避免上下文过大）                                  |
| 定位     | 工具使用"教科书"——教 Agent 何时、如何安全调用 tool              |

---

---

## 四、安全与边界

| 机制              | 说明                             |
| --------------- | ------------------------------ |
| MEMORY.md 不注入群聊 | 防隐私泄露                          |
| 大文件自动截断         | 防止 token 爆炸                    |
| Skills 权限过滤     | 可配置 environment / binary check |
| `/context` 命令   | 查看实际注入大小                       |

---

## 五、一句话总结

| 文件        | 类比     |
| --------- | ------ |
| AGENTS.md | 宪法（规则） |
| SOUL.md   | 灵魂（个性） |
| MEMORY.md | 记忆（经验） |
| TOOLS.md  | 本地配置   |
| SKILL.md  | 技能手册   |

它们通过 **Context Injection** 统一打包成 LLM 每次思考的"初始大脑状态"。