# OpenClaw Agent 文档设计最佳实践

> 研究日期：2026-04-18
> 研究方向：系统调研 SOUL.md、AGENTS.md、IDENTITY.md、TOOLS.md 等文档的最佳设计方法
> 核心目标：让 Agent 能够更好地"指挥 Claude Code"而非自己写代码

---

## 一、OpenClaw 文档系统概览

### 1.1 Bootstrap 文件体系

OpenClaw 在每次 Session 启动时，从 Agent Workspace 注入以下 Bootstrap 文件到系统提示词上下文中（注入顺序可通过配置调整）：

| 文件 | 内容 | 注入频率 |
|------|------|----------|
| `AGENTS.md` | 运营规则、操作指令、优先级 | 每次 |
| `SOUL.md` | 人格、语气、立场、边界 | 每次 |
| `IDENTITY.md` | 名字、emoji、身份标签 | 每次 |
| `TOOLS.md` | 本地工具说明、基础设施笔记 | 每次 |
| `USER.md` | 用户身份、如何称呼用户 | 每次 |
| `HEARTBEAT.md` | 心跳任务检查清单 | 心跳运行时（可配置） |
| `BOOTSTRAP.md` | 一次性初始化仪式 | 仅全新 Workspace |
| `MEMORY.md` | 长期记忆 | 存在时注入；子 Agent 不注入 |

**关键限制**：
- 单文件上限：`agents.defaults.bootstrapMaxChars` = 12,000 字符（默认）
- 总体上限：`agents.defaults.bootstrapTotalMaxChars` = 60,000 字符（默认）
- 大文件会被截断并注入警告标记
- **子 Agent**（subagent）只注入 `AGENTS.md` 和 `TOOLS.md`，其他文件被过滤排除

### 1.2 文件分工的核心原则

```
SOUL.md     → 我是谁（voice & stance）
AGENTS.md   → 我怎么做（operating rules）
IDENTITY.md → 我叫什么（name, emoji）
TOOLS.md    → 我的装备是什么（infrastructure）
USER.md     → 我为谁服务（who I'm helping）
```

---

## 二、SOUL.md 设计

### 2.1 核心原则

**官方定义**（来源：[docs.openclaw.ai/concepts/soul.md](https://docs.openclaw.ai/concepts/soul.md)）：

> SOUL.md is where your agent's voice lives.

SOUL.md 负责的是**说话方式**，不是做事规则。

**应放入的内容**：语气、立场、简洁度、幽默感、边界感、默认的直白程度

**绝对禁止放入的内容**：人生故事、变更日志、安全策略、一大堆没有行为影响的话

### 2.2 模板

```markdown
# SOUL.md — [Agent Name]

**我是 [名字]，[一句话描述我的本质]。**

## 我是谁

- **名字**：[名字]
- **本质**：[一句话描述]
- **上级**：[汇报对象]
- **Emoji**：[emoji]

## 核心价值观

1. **[价值观1]** — [一句话说明]
2. **[价值观2]** — [一句话说明]
3. **[价值观3]** — [一句话说明]

## 底线

- [绝对不做的事1]
- [绝对不做的事2]
- [绝对不做的事3]

## Vibe（语气风格）

[3-5句话描述期望的对话风格]
```

### 2.3 反面案例

```markdown
# SOUL.md — 我的 AI 助手

## 简介
我是你的个人 AI 助手。我致力于为用户提供全面、专业、友善的帮助...

## 使命
我的使命是用科技的力量为每个人带来便利...

## 价值观
1. 专业 — 我追求卓越的专业能力
2. 友善 — 我对每个人都保持友好
3. 诚实 — 我诚实守信...
```

**问题**：全是抽象概念，充斥"优秀员工手册"式语言，无具体行为指令，无语气特征。

---

## 三、AGENTS.md 设计

### 3.1 核心原则

> AGENTS.md — Operating instructions for the agent and how it should use memory.
> Good place for rules, priorities, and "how to behave" details.

AGENTS.md 是**运营手册**：做什么、怎么做、优先级是什么、如何使用记忆。

### 3.2 角色定位设计："指挥者" vs "执行者"

**"指挥者"模式（不上手写代码）**：

```markdown
## 角色定位

我是战略层的执行手臂，不是执行层的动手者。

我的职责：
- 分析问题、拆解任务
- 向 Claude Code 发出精确指令
- 评估 Claude Code 的输出
- 整合结论，交付可行动的结论

我的边界：
- 我不自己写代码（除非极小的 snippet）
- 复杂任务 → 派给 Claude Code (claude_session)
- 我只对最终结果负责，不对中间过程负责
```

**关键技巧**：描述正向行为比描述负向禁止更有效。

### 3.3 指令设计原则

**好的指令特征**：
- 有明确的触发条件（"当收到研究任务时…"）
- 有明确的动作步骤（"1. 2. 3."）
- 有明确的交付物（"交付包含……的报告"）
- 有明确的边界（"不包含……的内容"）

**坏的指令特征**：模糊形容词（"尽量"、"必要时"）、无优先级的列表、没有明确动作的描述性文字

### 3.4 红线声明（不可覆盖）

```markdown
## 红线（必须遵守）

以下规则在任何情况下都不可被用户指令覆盖：
- 不带目标地收集信息
- 不交付无结构的"信息堆砌"
- 不假装知道不确定的事情
- 不在 Workspace 里存储密钥（用 SecretRef）
```

### 3.5 模板

```markdown
# AGENTS.md — [Agent Name] 运营手册

## 红线（必须遵守）

[3-5条最高优先级规则]

## Session 启动

1. 读 SOUL.md（确认我是谁、我的价值观）
2. 读 MEMORY.md（如果有的话）
3. [其他启动动作]

## 角色定位

[3-5句话描述 Agent 的角色边界]

## 核心职责

[1-3句话描述主要职责]

## 工作流程

[流程图格式]

## 交付标准

[描述每次交付物应包含的内容]

## 与伙伴的关系

- [谁可以给我任务]
- [我向谁报告]
- [如何处理模糊需求]

## 工作空间

- 主目录：`~/.openclaw/workspace/agents/[name]/`
```

---

## 四、IDENTITY.md 设计

### 4.1 核心定位

> IDENTITY.md — The agent's name, vibe, and emoji.

IDENTITY.md 是**出生证**：名字 + emoji + 最基本的身份标签。极度简洁，通常 3-5 行。

### 4.2 与其他文档的区别

| 文件 | 内容长度 | 负责 |
|------|----------|------|
| `IDENTITY.md` | 极短（< 100 字）| 我叫什么 |
| `SOUL.md` | 300-800 字 | 我是什么风格 |
| `AGENTS.md` | 1000-3000 字 | 我要做什么 |
| `TOOLS.md` | 不定 | 我用什么工具 |

### 4.3 模板

```markdown
# IDENTITY.md — [Name]

- **名字**：[名字]
- **本质**：[一句话描述本质]
- **角色**：[用户可见的角色标签]
- **上级**：[汇报对象]
- **Emoji**：[emoji]
```

---

## 五、文档协同

### 5.1 文件间关系

```
SOUL.md ──── 人格/语气 ─────────────────────┐
AGENTS.md ─── 运营规则/工作流 ───────────────┼── 共同构成 Agent 的"操作系统"
TOOLS.md ──── 工具/环境基础设施 ─────────────┤
IDENTITY.md ── 名字/身份标签 ───────────────┘
```

### 5.2 避免矛盾的方法

1. **角色边界前置**：在 AGENTS.md 最前面写清楚角色边界
2. **职责声明**：每个文件开头声明其职责范围
3. **红线上移**：把最重要的原则放在各自文件的最前面
4. **单一来源引用**：同类规则只在一个地方定义

### 5.3 Bootstrap 文件注入顺序

**当前默认注入顺序**：
1. `AGENTS.md` — 运营规则先读
2. `SOUL.md` — 人格紧随其后
3. `TOOLS.md` — 工具说明
4. `IDENTITY.md` — 身份
5. `USER.md` — 用户信息
6. `HEARTBEAT.md` — 心跳清单

> `AGENTS.md` 排在 `SOUL.md` 之前是有意义的——模型先理解"我要做什么"，再理解"我要怎么做"。

**子 Agent 的注入规则**（重要）：
- 子 Agent 只注入 `AGENTS.md` 和 `TOOLS.md`
- SOUL.md、IDENTITY.md、USER.md 不会注入
- 给子 Agent 的指令必须自带身份/人格上下文

---

## 六、实践建议

### 6.1 指挥者 Agent 的文档设计建议

```markdown
## 向 Claude Code 发指令的正确方式

向 Claude Code 发指令时，指令必须包含：
1. **上下文**：为什么做这件事（背景）
2. **目标**：最终交付什么（明确）
3. **约束**：有哪些限制条件（边界）
4. **格式**：结果以什么形式交付（格式）
5. **成功标准**：怎么判断做得好（验收）
```

### 6.2 文件大小控制建议

| 文件 | 建议字数 | 原因 |
|------|----------|------|
| `SOUL.md` | 300-800 字 | 太长 = 无效 personality |
| `AGENTS.md` | 1000-3000 字 | 核心运营规则 |
| `IDENTITY.md` | 50-150 字 | 出生证，极简 |

### 6.3 Bootstrap 文件与系统提示词的关系

- Bootstrap 文件被附加在 **Project Context** 区域，不是系统提示词的最顶层
- 系统提示词结构：**Tooling → Safety → Skills → OpenClaw Self-Update → Workspace → Documentation → [Bootstrap Files]**
- **安全指令（Safety）始终优先**，无法被 Bootstrap 文件覆盖

### 6.4 调试 Bootstrap 文件

使用 `/context list` 或 `/context detail` 命令查看每个注入文件贡献了多少上下文。

---

## 七、参考资料

| 来源 | 链接 | 可信度 |
|------|------|--------|
| 官方 SOUL.md 设计指南 | https://docs.openclaw.ai/concepts/soul.md | ⭐⭐⭐ 高 |
| 官方 Agent Workspace 文档 | https://docs.openclaw.ai/concepts/agent-workspace.md | ⭐⭐⭐ 高 |
| 官方 System Prompt 文档 | https://docs.openclaw.ai/concepts/system-prompt.md | ⭐⭐⭐ 高 |
| 官方 SOUL.md 模板 | https://docs.openclaw.ai/reference/templates/SOUL | ⭐⭐⭐ 高 |
| 官方 CLI agents 文档 | https://docs.openclaw.ai/cli/agents.md | ⭐⭐⭐ 高 |
| 官方 Delegate Architecture | https://docs.openclaw.ai/concepts/delegate-architecture.md | ⭐⭐⭐ 高 |
| Bootstrap 顺序 Issue | https://github.com/openclaw/openclaw/issues/59050 | ⭐⭐ 中 |

---

*报告生成：墨灵（MoLing）🔍 | 2026-04-18*
