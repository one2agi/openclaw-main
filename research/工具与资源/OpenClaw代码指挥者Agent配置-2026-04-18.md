# 代码指挥者 Agent 配置研究

**研究日期：** 2026-04-18  
**研究者：** 墨灵  
**研究目标：** 为"指挥 Claude Code 写代码"的 OpenClaw Agent 推荐 Skills 配置与 CC 接通协议  
**数据来源：** OpenClaw 源码分析 + 现有 Agent 配置（code-dev/无极）参考

---

## 一、推荐 Skills 组合

### 1.1 必须启用（Mandatory）

#### ✅ `cc-director`
- **类型：** 工作流 SOP
- **来源：** `openclaw-workspace`（已就绪）
- **作用：** 任务分类（6类）→ 澄清 → 拆解 → 委托 → 审查 → 交付的完整流程规范
- **为什么必须：** 这是代码指挥的核心方法论。没有它，Agent 无法系统性地区分 Bugfix/功能/重构等任务类型，指令质量不可控
- **调用时机：** 每次给 CC 下达任务前必须读取执行

#### ✅ `claude-code-master`
- **类型：** 提示词 + 配置指南
- **来源：** `openclaw-workspace`（已就绪）
- **作用：** 
  - `@references/prompts.md` — CC 任务提示词模板库（T1-T9 各类型全覆盖）
  - `@references/config.md` — CLAUDE.md 编写规范
  - `@references/anti-patterns.md` — CC 常犯错误及纠正方案
- **为什么必须：** cc-director 的"委托执行"依赖 claude-code-master 的模板库，两者协同工作

#### ✅ `acp-router`
- **类型：** 路由协议
- **来源：** `openclaw-extra`（当前 disabled，需启用）
- **作用：** 
  - 统一路由外部编码 Agent（Claude Code / Codex / Cursor 等）的请求
  - 明确指定使用 `sessions_spawn`（而非 subagent runtime）
  - 定义了 agentId 映射规则（如 `"claude code" → agentId: "claude"`）
- **为什么必须：** 这是 CC 集成的官方规范路径，定义了在 OpenClaw ACP runtime 中如何正确地 spawn CC 会话

### 1.2 强烈推荐（Recommended）

#### ✅ `claude-code-skill`
- **类型：** MCP 协议控制
- **来源：** `openclaw-workspace`（已就绪）
- **作用：** 通过 MCP 协议直接控制 Claude Code，执行命令、读写文件、搜索代码
- **使用场景：** 当需要以 MCP client 身份调用 CC 而非通过 sessions_spawn 时
- **注意：** 与 `sessions_spawn` 是互补关系；`sessions_spawn` 用于多轮对话任务，`claude-code-skill` 用于细粒度工具调用

#### ✅ `lesson`
- **类型：** 知识沉淀
- **来源：** `openclaw-workspace`（已就绪）
- **作用：** 将 CC 执行中的教训存入 `learnings/`，形成 Agent 进化机制
- **为什么推荐：** 指挥 CC 是一个需要持续优化的能力，教训沉淀是 AGENTS.md 中"知识晋升机制"的核心工具

#### ✅ `taskflow`
- **类型：** 长周期任务流管理
- **来源：** `openclaw-bundled`（已就绪）
- **作用：** 管理跨多个 detached task 的工作流，保持单一 owner 上下文
- **使用场景：** 大型多步骤开发任务（如 TDD 流程中的 Red→Green→Refactor）

### 1.3 可选（Optional）

| Skill | 场景 | 优先级 |
|-------|------|--------|
| `in-depth-research` | 需要先调研技术方案再委托 CC | 中 |
| `self-evolution` | 自动化执行后经验沉淀 | 中 |
| `agent-browser` | CC 完成后需要浏览器验证 | 低 |
| `skill-creator` | 需要将 CC 指挥最佳实践固化为新 Skill | 低 |

### 1.4 应禁用的冲突 Skills

| Skill | 冲突原因 |
|-------|---------|
| `coding-agent` | 与 cc-director/acp-router 功能重叠，会产生路由混乱 |
| `agent-creator` | 与代码指挥无关，属于 Agent 创建工具 |

---

## 二、CC 接通协议选择

### 2.1 三种协议对比

| 维度 | `sessions_spawn` (runtime="acp") | `sessions_spawn` (runtime="subagent") | `claude_session_start` |
|------|-------------------------------|-------------------------------------|----------------------|
| **本质** | OpenClaw ACP runtime 托管外部 Agent 会话 | OpenClaw 原生 subagent 会话 | 直接启动 Claude Code CLI 子进程 |
| **适用 Agent** | Claude Code, Codex, Cursor 等外部编码 Agent | OpenClaw 内置 subagent | Claude Code（单一目标） |
| **会话管理** | ACP 线程模型，支持持久化会话 + 会话间上下文 | OpenClaw subagent 生命周期管理 | 独立 Claude Code 进程 |
| **多轮对话** | ✅ 支持，`sessions_send` 持续发消息 | ✅ 支持 | ✅ 支持，`claude_session_send` |
| **MCP 工具支持** | ✅ 通过 acpx 代理 | ❌ 不支持 MCP | ✅ 原生 Claude Code MCP 工具 |
| **权限控制** | 通过 acpx 代理层，粒度较粗 | OpenClaw subagent 权限体系 | Claude Code 原生权限模式 |
| **thread 支持** | ✅（`thread: true` 参数）| ❌ | ❌ |
| **会话命名** | ACP 风格 `cc-[类型]-[描述]` | subagent session name | 自定义 session name |
| **上下文压缩** | 通过 ACP 会话管理 | OpenClaw 自动管理 | `/compact` 命令 |
| **Agent 间通信** | ✅ acp 内部消息传递 | ❌ subagent 间无法直接通信 | ❌ |
| **复杂性** | 中等，需 acp-router 规范 | 低 | 低 |
| **文档规范** | acp-router SKILL.md 明确定义 | OpenClaw 通用文档 | Claude Code 官方文档 |

### 2.2 推荐决策树

```
下达任务给 Claude Code
        │
        ▼
是否需要多轮对话 + 线程上下文？
        │
   Yes  │  No
    ┌───┘  └──┐
    ▼          ▼
acp runtime   一次性任务？
路径           │
    │          ├─ 需要持久会话 → sessions_spawn(runtime="acp")
    │          └─ 不需要持久 → claude_session_start + 一条消息
    │
    ▼
sessions_spawn({
  runtime: "acp",
  agentId: "claude",
  thread: true,
  mode: "session",
  task: "...",
  label: "cc-[类型]-[描述]"
})
```

### 2.3 场景对应表

| 场景 | 推荐协议 | 具体调用 |
|------|---------|---------|
| **指挥 CC 执行新任务，多轮对话** | `sessions_spawn` (runtime="acp") | `sessions_spawn({ runtime: "acp", agentId: "claude", thread: true, mode: "session", task, label })` |
| **继续已有 CC 会话** | `sessions_send` | `claude_session_send(name, message)` 或 ACP 路径消息 |
| **一次性 CC 查询/小修复** | `sessions_spawn` (runtime="acp") | `sessions_spawn({ runtime: "acp", agentId: "claude", mode: "one-shot", task })` |
| **需要 MCP 细粒度工具控制** | `claude_session_start` | `claude_session_start(name, engine="claude")` |
| **多 CC 并行子任务** | `sessions_spawn` × N (runtime="acp") | 每任务一个 session，最多 2 个并行 |
| **内部 OpenClaw subagent 任务** | `sessions_spawn` (runtime="subagent") | 纯 OpenClaw 能力，非 CC 场景 |
| **通过 acpx CLI 直接驱动 CC** | exec 调用 acpx | ACP 规范中的 telephone-game 路径 |

### 2.4 协议选择的核心原则

1. **指挥外部编码 Agent → `runtime="acp"`**  
   这是 OpenClaw 的官方集成路径。acp-router 明确要求：对 Claude Code/Codex/Cursor 等外部 Agent 的请求，必须使用 `sessions_spawn(runtime="acp")`，禁止使用 subagent runtime

2. **`runtime="subagent"` 仅用于**  
   OpenClaw 内部的 subagent 任务，与 CC 完全无关

3. **`claude_session_start` 作为补充**  
   当需要直接控制 Claude Code CLI 进程、获取完整 MCP 工具集、或与现有 Claude Code 配置深度集成时使用

---

## 三、代码指挥者 Agent 配置示例

### 3.1 Agent 定义文件结构

```
~/.openclaw/workspace/agents/code-director/
├── AGENTS.md          # 运营手册（任务分类、流程）
├── SOUL.md            # 角色定义（技术总监/指挥官人格）
├── IDENTITY.md        # 身份标识
├── USER.md            # 用户画像
├── MEMORY.md          # 长期记忆
├── TOOLS.md           # 工具配置说明
├── memory/
│   └── projects/      # 项目级知识
├── learnings/         # CC 教训沉淀
│   └── LEARNINGS.md
└── skills/            # 本 Agent 专属 Skills（可选覆盖全局）
    └── cc-director/   # 优先使用本地版本
```

### 3.2 AGENTS.md 核心片段

```markdown
## 五、CC 委托协议（强制）

每次给 CC 下达任务，必须：
1. 读取 `cc-director` skill — 执行任务分类 SOP
2. 读取 `claude-code-master` — 选择对应提示词模板
3. 调用 `sessions_spawn(runtime="acp", agentId="claude")` — 禁止 subagent runtime

### sessions_spawn 标准参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `runtime` | `"acp"` | 必须，ACPT 托管路径 |
| `agentId` | `"claude"` | 固定值 |
| `thread` | `true` | 多轮对话场景开启 |
| `mode` | `"session"` | 持久会话 |
| `label` | `"cc-[T1-T9]-[简短描述]"` | 会话标识 |
| `runTimeoutSeconds` | `300`（常规）/ `600`（大型） | 超时控制 |

### 禁止事项

- ❌ 禁止用 `runtime="subagent"` 委托 CC 任务
- ❌ 禁止跳过 cc-director SOP 直接发任务
- ❌ 禁止不给验收标准就交付 CC 产出
- ❌ 禁止不审查直接交付 CC 代码
```

### 3.3 sessions_spawn 调用示例

**场景：T2 功能开发，多轮对话**

```json
{
  "runtime": "acp",
  "agentId": "claude",
  "label": "cc-t2-feature-login",
  "thread": true,
  "mode": "session",
  "task": "【背景】现有 Node.js 项目，Express 框架...\n\n【目标】实现 JWT 登录...\n\n【验收标准】\n- [ ] POST /api/login 返回 token\n- [ ] 已有 Jest 测试通过\n\n【参考文件】\n@src/auth/login.js",
  "runTimeoutSeconds": 600
}
```

**场景：T1 Bugfix，一次性**

```json
{
  "runtime": "acp",
  "agentId": "claude",
  "label": "cc-t1-bugfix-401",
  "thread": false,
  "mode": "one-shot",
  "task": "修复：用户登录后访问 /api/me 返回 401...\n\n【错误信息】...\n\n【验收标准】\n- [ ] /api/me 返回当前用户信息\n- [ ] 现有测试全部通过",
  "runTimeoutSeconds": 300
}
```

### 3.4 cc-director × claude-code-master 协同流程

```
接收任务
    │
    ▼
cc-director: 任务分类（T1-T9）
    │
    ├── T4 技术调研？→ 先调用 in-depth-research
    │
    ▼
cc-director: 需求澄清（需求不清晰时）
    │
    ▼
cc-director: 任务拆解（多文件/多步骤）
    │
    ▼
claude-code-master: 选择 prompts.md 模板
    │
    ▼
生成指令（背景+目标+约束+验收标准）
    │
    ▼
sessions_spawn(runtime="acp", ...) 派给 CC
    │
    ▼
审查结果（cc-director 第六章审查标准）
    │
    ├── 通过 → 交付
    └── 失败（≤2轮）→ 上报
    │
    ▼
lesson skill: 沉淀教训到 learnings/
```

---

## 四、最佳实践总结

### 4.1 Skills 启用策略

| 优先级 | 操作 |
|--------|------|
| **立即启用** | `acp-router`（当前 disabled） |
| **已就绪确认** | `cc-director`、`claude-code-master`、`claude-code-skill`、`lesson`、`taskflow` |
| **已就绪可选** | `in-depth-research`、`self-evolution` |
| **保持禁用** | `coding-agent`（与 acp-router 冲突） |

### 4.2 CC 集成三原则

1. **ACPT runtime 优先**：`sessions_spawn(runtime="acp")` 是指挥 CC 的标准路径，任何场景都先尝试 ACP
2. **thread 模型隔离**：不同任务用不同 thread，同任务多轮在同一 thread
3. **审查不过不交付**：cc-director 的质量门控是硬性要求，不可跳过

### 4.3 已验证的 Agent 配置参考

**code-dev（无极）** 是当前 faiz 团队中运行最成熟的代码指挥 Agent，其 Skills 配置直接验证了本研究的推荐方案：

```
~/.openclaw/workspace/agents/code-dev/skills/
├── cc-director/          ✅ 验证可行
├── claude-code-master/  ✅ 验证可行
├── in-depth-research/   ✅ 验证可行
├── lesson/              ✅ 验证可行
├── self-evolution/      ✅ 验证可行
└── skill-creator/       ✅ 验证可行（Skill 创建）
```

---

## 五、报告信息

- **数据时效性：** 基于 2026-04-18 的 OpenClaw 源码分析
- **研究置信度：** 高（主要参考现有运行中的 code-dev Agent + acp-router 源码）
- **待验证项：** `acp-router` 在实际运行时是否需要 gateway restart 配合（acp-router SKILL.md 中有相关描述）
