# OpenClaw 社区 Agent 设计经验

**研究时间：2026-04-18**
**来源：Reddit (r/openclaw)、dev.to、GitHub、OpenClaw 官方文档、Stack-Junkie、ComputerTech.co**

---

## 社区共识

### 最佳实践

**1. SOUL.md 与 AGENTS.md 职责分离**
- **SOUL.md** → 核心身份与人格（很少变动）
- **AGENTS.md** → 操作规则与自主权限（执行逻辑）
- Reddit 高赞经验："保持 SOUL.md 精简，把所有程序性逻辑移到 AGENTS.md，行为更一致"
- 来源：r/openclaw, 2026-03-05

**2. 身份描述要具体到"有血有肉"**
- 泛泛地说"You are helpful" = 得到最无聊的 AI 回复
- 好的写法示例："Talk like a tradesman who happens to know code — not a consultant who read a blog about blue collar life. Swear when it fits."
- 差异：泛泛描述 → 听起来像 chatbot；具体描述 → 像真人
- 来源：computertech.co

**3. 加入反谄媚规则（Anti-sycophancy Rule）**
- AI 默认训练是"顺从的"，会软化批评、认可弱想法
- 明确写入：AI 应该在某些事不对劲时直接 push back
- "That's a bad idea because X, here's what I'd do instead."
- 这条规则被多个社区成员评为"写的时候觉得怪，但实际价值最高的一条"
- 来源：computertech.co

**4. AGENTS.md 用"直接做"vs"先问"的二分法**
- **直接做**：对已确立方向的行动（修复 bug、更新已发布内容、跑研究 sub-agent）
- **先问**：涉及新方向、支出、破坏性操作
- 原则："这是一个已确立方向还是新方向？" 已确立 → 做并报告；新 → 先提议
- 来源：computertech.co

**5. 记忆系统要写死规则**
- 决策 → `memory/handoff.md`
- 计划 → `memory/active-projects.md`
- 教训 → `memory/lessons.md`
- 复杂工作超过 2 小时 → 建议 /new 并记录到 handoff.md
- "If a rule matters, it goes in AGENTS.md. If you correct the agent, it goes in MEMORY.md. If it's only in the chat, it's gone next session."
- 来源：r/openclaw, 2026-03-15

**6. 上下文分层架构**
```
SOUL.md        — 核心身份（稳定）
USER.md        — 用户信息
MEMORY.md      — 长期上下文
memory/YYYY-MM-DD.md — 每日会话笔记
```
- 来源：dev.to SOUL.md 指南

**7. 赋予 Agent 战略视角**
- 在 SOUL.md 中明确优先级："Priority: [Project A] > [Project B] > everything else"
- 当用户问"今天做什么"时，AI 不会把所有活动当作等价的，而是通过同一镜头过滤
- 来源：computertech.co

**8. 多 Agent 场景用 peer-to-peer 而非 sub-agent**
- OpenClaw sub-agent 模型适合"主 Agent 把子任务委托给助手"
- peer-to-peer agent 通信（agentToAgent）+ sessions_send 可寻址会话
- 多 Agent 开发管道用 Lobster（OpenClaw 工作流引擎）+ 子工作流 + 循环支持
- 来源：dev.to ggondim 的多 Agent 开发管道实践，2026-02-23

**9. 每个 Agent 独立的 agentDir，绝不共享**
- auth profiles、session store、workspace 完全隔离
- 想共享凭证 → 复制 `auth-profiles.json` 到其他 agentDir
- 共享 agentDir → auth/session 冲突
- 来源：OpenClaw 官方多 Agent 文档

---

### 常见错误

**1. SOUL.md 太泛泛（比没有还糟）**
- "Be helpful and professional" → 得到最无聊的 AI 回复
- 社区反馈：默认的 SOUL.md 和 AGENTS.md 极度泛泛，不告诉 agent 你是谁、工作流什么样、边界在哪里
- 来源：r/AI_Agents, 2026-02-04

**2. 把所有东西都塞进 SOUL.md**
- SOUL.md 过大 → token 浪费，行为不一致
- 最佳实践：SOUL.md 保持精简，操作逻辑放 AGENTS.md
- 来源：r/openclaw, 2026-03-05

**3. 记忆只存在于聊天中**
- 聊天内容 → 下次会话消失
- 规则：需要记住的内容必须进 AGENTS.md 或 MEMORY.md
- 来源：r/openclaw, 2026-03-15

**4. 把 sub-agent 用于 peer-to-peer 协作**
- sub-agent 模型：深度限制 1-2，父 LLM 控制流程（非确定性）
- 想做管道/编排 → 用 Lobster 工作流 + agentToAgent peer messaging
- 来源：dev.to ggondim

**5. 多 Agent 场景共享 agentDir**
- 导致 auth 冲突和 session 碰撞
- 每个 agent 必须有独立的 `~/.openclaw/agents/<agentId>/`
- 来源：OpenClaw 官方多 Agent 文档

**6. 过度配置导致系统退化**
- "系统不会因为一个大错误崩溃，而是因为善意的小改进不断退化"
- 表现：用户频繁修改 SOUL.md/AGENTS.md，每次修改都在 agent 行为中引入新问题
- 来源：Facebook OpenClaw 社区，2026-03-19

**7. 权限规则不够细**
- 只写"can do X"而不写"cannot do Y"
- 破坏性命令没有明确边界："Never execute destructive commands (rm -rf, DROP TABLE) without explicit confirmation"
- 来源：dev.to SOUL.md 指南

---

## 优秀案例

### 案例1：OpenClaw Production Templates（Sargentech-AI）
- **链接**：`https://github.com/Sargentech-AI/openclaw-production-templates`
- **结构**：生产级配置模板，来源 6+ 月多 Agent 生产栈，经过现实检验的 pattern 集合
- **优点**：开箱即用，经过真实生产环境验证
- **可信度**：⭐⭐⭐⭐⭐（GitHub 生产模板，真实场景验证）

### 案例2：shenhao-stu/openclaw-agents（9 Agent 协作套件）
- **链接**：`https://github.com/shenhao-stu/openclaw-agents`
- **结构**：预配置 9 个专业化 Agent 团队，完整的协作架构
- **优点**：展示了多 Agent 团队协作模式，非单一 agent
- **可信度**：⭐⭐⭐⭐（完整多 Agent 套件，社区活跃）

### 案例3：Atlas SOUL.md 模板（dev.to 指南）
- **链接**：`https://dev.to/techfind777/the-ultimate-guide-to-writing-soulmd-for-openclaw-agents-12a1`
- **结构**：Identity + Style + Stack + Principles + Rules 完整五段式
- **优点**：展示了决策框架（Decision Framework），包括"安全 > 便利"、"选择无聊的技术"
- **可信度**：⭐⭐⭐⭐（详细的 SOUL.md 写作指南，含真实模板）

### 案例4：ComputerTech 运营手册型 Agent
- **链接**：`https://computertech.co/openclaw-workspace-files-explained-soul-md-agents-md-and-user-md-2026/`
- **结构**：SOUL.md（身份+反谄媚规则+战略优先级）+ AGENTS.md（直接做/先问列表+责任区+记忆系统规则）
- **优点**：记忆系统规则化、权限分级、主动型 Agent 行为（不是等被问，而是主动 surface 被忽略的项目）
- **可信度**：⭐⭐⭐⭐⭐（1 年以上实际运营经验，内容详尽）

### 案例5：ggondim 多 Agent 开发管道（Lobster 架构）
- **链接**：`https://dev.to/ggondim/how-i-built-a-deterministic-multi-agent-dev-pipeline-inside-openclaw-and-contributed-a-missing-4ool`
- **结构**：programmer → reviewer → tester 管道，Lobster YAML 工作流 + agentToAgent peer messaging
- **优点**：展示了 OpenClaw sub-agent 真实限制（深度限制 1-2，并发限制 8）和正确解法
- **可信度**：⭐⭐⭐⭐⭐（含 PR 贡献记录，深度技术实践）

---

## 问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Agent 行为像 generic chatbot | SOUL.md 太泛泛 | 用具体身份描述 + 反谄媚规则 |
| Agent 不记得上次会话内容 | 记忆没写进文件 | AGENTS.md 中写记忆系统规则，MEMORY.md 持久化 |
| 多 Agent 协作流程不可控 | 用了 sub-agent 做 peer-to-peer | 用 Lobster 工作流 + agentToAgent |
| agentDir auth 冲突 | 多个 agent 共享了 agentDir | 每个 agent 独立 agentDir |
| 规则变更后行为不一致 | 改在聊天中说，没进文件 | 规则进 AGENTS.md，纠正进 MEMORY.md |
| 过度配置导致退化 | 频繁修改 SOUL.md/AGENTS.md | 保持 SOUL.md 精简，变更走 MEMORY.md |
| Sub-agent 返回空 | 深度限制或 auth/quota 错误 | 检查 openclaw logs --follow |

---

## 来源汇总

| # | 来源 | 类型 | 可信度 |
|---|------|------|--------|
| 1 | r/openclaw（SOUL.md critique 帖） | Reddit 社区 | ⭐⭐⭐⭐ |
| 2 | r/openclaw（系统架构帖子） | Reddit 社区 | ⭐⭐⭐⭐ |
| 3 | r/openclaw（Agent 可靠性帖） | Reddit 社区 | ⭐⭐⭐ |
| 4 | dev.to SOUL.md 终极指南 | 技术博客 | ⭐⭐⭐⭐ |
| 5 | computertech.co 工作空间文件详解 | 技术博客 | ⭐⭐⭐⭐⭐ |
| 6 | dev.to 多 Agent 开发管道 | 技术博客 + PR | ⭐⭐⭐⭐⭐ |
| 7 | docs.openclaw.ai 多 Agent 文档 | 官方文档 | ⭐⭐⭐⭐⭐ |
| 8 | GitHub: Sargentech-AI/openclaw-production-templates | GitHub 仓库 | ⭐⭐⭐⭐ |
| 9 | GitHub: shenhao-stu/openclaw-agents | GitHub 仓库 | ⭐⭐⭐⭐ |

---

*⚠️ 局限性：Reddit 大量内容无法直接访问（IP 限制），基于摘要片段；Discord 社区内容未直接获取；GitHub 仓库内容未直接读取完整文件。置信度：中偏低。*
