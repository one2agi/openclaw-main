# OpenClaw 多 Agent 持久化上下文交流机制

> 研究时间：2026-05-06
> 来源：OpenClaw 官方文档（docs/concepts/multi-agent.md / subagents.md / session.md）

---

## ⚡ 一句话结论

OpenClaw 的多 Agent 上下文共享靠 **Session 隔离 + 文件记忆 + 消息驱动** 三层机制实现，并非共享内存，而是通过推送式 announce + QMD 向量检索实现跨 Agent 上下文延续。

---

## 一、核心架构：隔离 + 轻量共享

**每个 Agent 有独立的上下文空间：**

```
~/.openclaw/agents/<agentId>/
├── sessions/              ← 独立 session store + transcript
│   ├── sessions.json
│   └── <sessionId>.jsonl
├── agent/                 ← auth profiles、model registry
└── workspace/             ← 独立文件系统
```

**Agent 间默认不共享 session transcript**，但可以通过以下机制实现上下文传递。

---

## 二、上下文传递的 5 种机制

| 机制 | 触发方式 | 持久化 | 适用场景 |
|------|---------|--------|---------|
| **① Sub-agent Announce（推送回报）** | `sessions_spawn` | 结果推送回 requester chat | 任务完成通知 |
| **② sessions_send（消息发送）** | 工具调用 | 写入目标 session | 实时协作 |
| **③ sessions_history（历史拉取）** | 工具调用 | 只读 sanitized view | 跨 session 召回 |
| **④ QMD extraCollections（向量检索）** | 配置项 | 持久化到向量库 | 语义搜索历史 |
| **⑤ 文件系统共享** | 通过 workspace | 磁盘持久化 | 大块数据/报告 |

---

## 三、机制详解

### 机制①：Sub-agent Announce（最核心）

```
Main Agent → sessions_spawn → Sub-agent 执行 → announce 推送回 Main Agent
```

**关键参数：**

| 参数 | 含义 |
|------|------|
| `context: "isolated"`（默认） | 干净子 session，无历史包袱 |
| `context: "fork"` | 把当前 transcript 分支进子 session（用于需要上下文连贯的场景） |
| `mode: "run"` | 一次性任务，完成后 announce 结果 |
| `mode: "session"` | 持续性 session，需配合 thread: true |
| `thread: true` | 绑定到 Channel thread，支持后续跟进对话 |

**Announce 推送内容：**

- 最新可见 assistant 回复文本
- 运行时间 / token 统计
- 状态（success / failed / timeout）

**Announce 推送机制：**
- OpenClaw 先尝试 direct agent 投递（幂等 key）
- 失败则回退到 queue routing
- 再失败则 exponential backoff 重试后放弃

**注意：** announce 是 best-effort 推送，gateway 重启会导致 pending announce 丢失。

---

### 机制②：sessions_send（双向实时通信）

一个 Agent 可以主动给另一个 Agent 发消息：

```javascript
sessions_send({
  sessionKey: "agent:targetAgentId:main",
  message: "任务已完成，结果如下：..."
})
```

目标 Agent 收到后追加到自己的 session 历史。

**限制：**

- 需要 `agentToAgent` 工具启用：`tools.agentToAgent.enabled: true`
- 需配置 `allow: ["agentA", "agentB"]` 白名单

---

### 机制③：sessions_history（跨 session 只读召回）

不是拉取完整 transcript，而是返回**经过安全过滤的 bounded view**：

- 移除 `<thinking>` 标签
- 移除原始 tool call XML payload（`<tool_call>` 等）
- 移除 credential-like 文本
- 长 block 可截断
- 超大历史可丢弃旧行

适合"另一个 Agent 的结论"类轻量引用。

---

### 机制④：QMD extraCollections（跨 Agent 语义搜索）

这是最接近"共享记忆"的设计：

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        qmd: {
          extraCollections: [
            { path: "~/agents/family/sessions", name: "family-sessions" }
          ]
        }
      }
    }
  }
}
```

- 路径在 workspace 内 → collection 名自动加上 agent 前缀（如 `notes-main`）
- 路径在 workspace 外 → collection 名保持显式（如 `family-sessions`）
- 本质是把另一个 Agent 的 session transcript 加入向量检索范围，实现语义级跨 Agent 记忆共享

---

### 机制⑤：文件系统（最原始但最可靠）

- 写文件到共享路径 → 其他 Agent 通过 `read` 工具获取
- 适合大块数据（报告、图片、JSON）
- 最可靠的跨 Agent 持久化方式（不受 session 生命周期影响）

---

## 四、Sub-agent 关键配置

### 嵌套深度控制

```json5
{
  agents: {
    defaults: {
      subagents: {
        maxSpawnDepth: 2,           // 允许一层嵌套（主 → 子 → 孙）
        maxChildrenPerAgent: 5,      // 每个 agent 最多 5 个活跃子 agent
        maxConcurrent: 8,            // 全局并发上限
        archiveAfterMinutes: 60      // 完成后 60 分钟自动归档
      }
    }
  }
}
```

**Orchestrator Pattern（编排者模式）：**
- `maxSpawnDepth: 1`（默认）：主 agent → 子 agent，不可再嵌套
- `maxSpawnDepth: 2`：主 agent → 编排 agent →  worker sub-agent（两层嵌套）

### 模型配置

Sub-agent 默认继承 caller 模型，可单独配置：

```json5
{
  agents: {
    defaults: {
      subagents: {
        model: "anthropic/claude-sonnet-4-6",  // 默认子 agent 模型
        runTimeoutSeconds: 300                   // 默认超时 5 分钟
      }
    }
  }
}
```

---

## 五、会话生命周期

### Session 存储位置

```
~/.openclaw/agents/<agentId>/sessions/
├── sessions.json      ← session store（生命周期管理）
└── <sessionId>.jsonl ← transcript 历史
```

### Session 重置策略

| 策略 | 触发条件 |
|------|---------|
| **每日重置** | 默认每天 4:00 AM 本地时间 |
| **空闲重置** | 可选，设置 `session.reset.idleMinutes` |
| **手动重置** | `/new` 或 `/reset` 指令 |

### Session 维护（自动清理）

```json5
{
  session: {
    maintenance: {
      mode: "enforce",       // warn（报告）/ enforce（自动清理）
      pruneAfter: "30d",    // 30 天后清理
      maxEntries: 500        // 最多 500 条记录
    }
  }
}
```

---

## 六、与 Manus 的对比

| 维度 | OpenClaw | Manus |
|------|---------|-------|
| **共享方式** | 推送 announce + 向量检索 | 共享云端 context |
| **隔离性** | Agent 间完全独立 session | 共享 planning/execution context |
| **跨 Agent 调用** | 需 explicit sessions_send | Planner → Executor 直接函数调用 |
| **上下文持久化** | Session transcript + QMD | 文件系统作为外部 context |
| **通信延迟** | Announce 推送（异步） | 进程内函数调用（同步） |
| **子 agent 嵌套** | 最多 2 层深度 | 多层嵌套架构 |

---

## 七、设计约束与注意事项

1. **Session 默认隔离**：不同 Agent 的 session 不自动共享，需显式配置
2. **Announce 不保证到达**：gateway 重启会导致 pending announce 丢失
3. **Fork 谨慎使用**：`context: "fork"` 会带入完整 transcript，成本高
4. **Sub-agent 默认无 session 工具**：无法自行拉取其他 session 的历史（除非显式授权）
5. **agentToAgent 默认关闭**：需配置 `tools.agentToAgent.enabled: true`
6. **Never reuse agentDir**：跨 Agent 的 agentDir 共享会导致 auth/session 冲突
7. **OAuth token 不跨 Agent 复制**：每个 Agent 需要独立登录授权

---

## 八、推荐实践

### 跨 Agent 共享大块结论（报告/数据）

```
Agent A（研究）→ 写入文件 → ~/workspace/shared/research.md
Agent B（执行）→ read → ~/workspace/shared/research.md
```

### 实时任务协作

```
Main Agent → sessions_spawn (context: "isolated") → Sub-agent（执行中）
     ↑ sessions_send（中间进度通知）
     ↑ Sub-agent → announce（最终结果）
```

### 语义级跨 Agent 记忆

```
配置 QMD extraCollections：
- Agent A 的 session transcript → 加入 Agent B 的向量检索范围
- 实现跨 Agent 的语义搜索（如"之前谁研究过这个主题"）
```

---

## 九、来源

| 文档 | 内容 |
|------|------|
| `docs/concepts/multi-agent.md` | 多 Agent 路由、binding、extraCollections |
| `docs/tools/subagents.md` | Sub-agent 生命周期、announce 机制、嵌套深度 |
| `docs/concepts/session.md` | Session 隔离、重置策略、维护机制 |
