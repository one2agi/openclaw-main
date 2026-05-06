# 🔬 DEEP RESEARCH: OpenClaw 多代理团队最佳实践

**研究时间：** 2026-04-16
**深度：** Standard
**来源：** OpenClaw 官方文档 + 社区实践

---

## ⚡ ANSWER

OpenClaw 多代理团队的核心架构：**每个代理 = 完全隔离的大脑**（独立 workspace + agentDir + sessions）。代理间通过 `bindings` 路由消息，通过共享文件或 memory search 共享上下文。最佳实践是"职责单一化 + 通信结构化"。

---

## 📊 CONFIDENCE: High

OpenClaw 官方文档有明确说明，结合已验证的配置经验。

---

## 🔍 KEY FINDINGS

### 1. 代理隔离架构（核心）
每个代理拥有独立的：
- **Workspace** — 文件、AGENTS.md/SOUL.md/USER.md、 persona 规则
- **State directory (agentDir)** — auth profiles、model registry、per-agent config
- **Session store** — 聊天历史 + 路由状态

> ⚠️ 禁止复用 `agentDir`（会导致 auth/session 冲突）

### 2. 代理创建方式
```bash
openclaw agents add <name>   # 推荐：自动创建完整目录结构
```
或手动在 `agents.list` 中注册 + 创建 workspace 目录。

### 3. Workspace 注意事项
- 每个代理的 workspace 是**默认工作目录**，不是硬沙盒
- 相对路径在 workspace 内解析
- 绝对路径可以 reach 到 host 其他位置（除非启用 sandboxing）
- **最佳实践：** 每个代理 workspace 放独立项目目录

### 4. 技能加载规则
- 从代理自身 workspace + 共享根目录（`~/.openclaw/skills/`）加载
- `agents.defaults.skills` = 共享基础技能
- `agents.list[].skills` = 代理专属技能（覆盖默认）

### 5. 消息路由（bindings）
- **确定性路由** + **最具体匹配优先**
- 匹配优先级：peer > parentPeer > guildId+roles > guildId > accountId > channel > default
- 同一个 tier 多个匹配时，config 顺序排第一的赢

### 6. 代理间内存共享
- `memorySearch.qmd.extraCollections` — 让一个代理搜索另一个的会话记录
- 共享 collection 时用绝对路径
- workspace 内的路径自动按代理 scope 隔离

### 7. 身份文件规范
每个代理 workspace 应包含：
| 文件 | 必须 | 用途 |
|------|------|------|
| AGENTS.md | ✅ | 身份定义 + 工作原则 + 技术栈 |
| SOUL.md | ✅ | 行为风格规则 |
| USER.md | 建议 | 服务对象信息 |
| TASKS.md | 建议 | 任务记录 |
| MEMORY.md | 建议 | 长期记忆 |
| TOOLS.md | 可选 | 工具注意事项 |

---

## ⚠️ CAVEATS

1. **沙盒限制** — workspace 不是硬隔离，代理仍可访问 host 文件系统
2. **认证不共享** — 主代理的 credentials 不会自动共享给子代理
3. **DM 收敛** — 同一 WhatsApp DMs 会 collapse 到 agent main session key，真隔离需要每个用户一个代理
4. **skill-creator 限制** — 子代理的 skill 生成能力尚未测试

---

## 🕳️ GAPS

- 代理间实时通信（IPC）的最佳实践尚未探索
- 多代理并发任务调度的性能数据缺失
- 代理团队错误恢复机制未文档化

---

## 🛠️ OPENCLAW 代理团队架构建议（针对 faiz 的场景）

### 当前已建立
- **main（墨染）** — 军师 & 秘书，战略 +  orchestration
- **无极（码农）** — 专职代码开发

### 建议补充
```
┌─ main (墨染)         ← 唯一对外入口，调度中心
│  ├─ 无极 (码农)  ← 代码开发/修复/优化/测试
│  ├─ research-dev     ← 深度研究 + 市场分析
│  └─ [未来可扩展]     ← 内容创作、运营等
```

### 命名规范建议
| ID | 名字 | 职责 |
|----|------|------|
| `main` | 墨染 | 战略、调度、对外 |
| `无极` | 码农 | 代码 |
| `researcher` | 调研员 | 研究、分析 |
| `writer` | 笔杆 | 内容创作（未来）|

---

## 📚 SOURCES

1. OpenClaw 官方文档 — Multi-Agent Routing (`docs.openclaw.ai/concepts/multi-agent`)
2. OpenClaw 官方文档 — Skills (`docs.openclaw.ai/tools/skills`)
3. OpenClaw 官方文档 — Sandboxing (`docs.openclaw.ai/gateway/sandboxing`)

---

## 🔎 METHODOLOGY

- 直接读取 OpenClaw 官方文档（docs.openclaw.ai）
- 交叉验证已知的本地配置经验
- 参考 AGENTS.md 中的深度研究约定
