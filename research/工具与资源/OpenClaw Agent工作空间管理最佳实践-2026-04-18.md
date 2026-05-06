# Agent 工作空间管理最佳实践
> 墨灵内部研究 | 2026-04-18 | 基于 OpenClaw 官方文档 + 社区实践

---

## 研究背景

本报告系统研究 OpenClaw Agent 如何通过工作空间（workspace）管理实现职责履行与持续进化。
数据来源：OpenClaw 官方文档（docs.openclaw.ai）、GitHub 源码文档、Playbook 实践文章、社区 skill 仓库（ClawHub/GitHub）。

---

## 一、工作空间组织

### 1.1 目录结构设计

**核心原则：workspace 是 agent 的"大脑"，而非文件系统。**

OpenClaw workspace 采用扁平的引导文件体系：

```
~/.openclaw/workspace/
├── AGENTS.md         # 操作指令（每次会话加载）
├── SOUL.md           # 人格与边界（每次会话加载）
├── USER.md           # 用户信息（每次会话加载）
├── IDENTITY.md       # 身份标识（轻量）
├── TOOLS.md          # 本地工具规范（指导而非控制）
├── HEARTBEAT.md      # 心跳任务清单（可选，极简）
├── BOOT.md           # 启动检查清单（可选）
├── BOOTSTRAP.md      # 首次运行仪式（一次性）
├── MEMORY.md         # 长期记忆（仅私信会话）
├── memory/           # 每日记忆目录
│   └── YYYY-MM-DD.md
├── skills/           # workspace 本地技能（最高优先级覆盖）
├── canvas/           # Canvas UI 文件
├── .learnings/       # 自我改进日志
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
└── research/         # 研究报告（按主题分子目录）
```

**注意：**
- `~/.openclaw/` 存放配置/凭证/会话，**不应**进入 workspace 版本控制
- workspace 与 `~/.openclaw/` 是分离的，"办公室"与"机房"的关系
- workspace 是默认 cwd，**非硬隔离沙箱**。如需隔离，需启用 `agents.defaults.sandbox`

---

### 1.2 Bootstrap 文件注入机制

OpenClaw 在每个会话开始时将 bootstrap 文件注入上下文。关键参数：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `agents.defaults.bootstrapMaxChars` | 20,000 | 单文件截断阈值 |
| `agents.defaults.bootstrapTotalMaxChars` | 150,000 | 总注入上限 |

**实践建议：**
- AGENTS.md 保持 **≤ 5,000 字**（结构化、优先级清晰）
- SOUL.md 保持 **≤ 1,000 字**（简洁有力）
- 大型内容外置到 `skills/`、`research/` 等子目录
- `openclaw setup` 可重建缺失的默认文件（不覆盖已有文件）

---

### 1.3 报告存放策略

墨灵当前实践（参考）：

```
主目录：~/.openclaw/workspace/agents/墨灵/
报告目录：~/.openclaw/workspace/research/（按主题分子目录）
```

**规范命名：**
- 研究报告：`YYYY-MM-DD-报告标题.md`
- HTML 可视化：与同名 `.html` 文件并置
- 符号链接指向全局 research 目录

**关键点：**
- md + HTML 双文件交付（AGENTS.md 规范）
- 符号链接避免 workspace 膨胀
- 不在 workspace 根目录直接放报告

---

### 1.4 Workspace 与 Bootstrap 文件的关系

Bootstrap 文件是 OpenClaw 的上下文注入机制，workspace 是物理位置：

| 文件类型 | 作用 | 加载时机 |
|---|---|---|
| AGENTS.md | 操作指令 | 每次会话 |
| SOUL.md | 人格定义 | 每次会话 |
| USER.md | 用户信息 | 每次会话 |
| HEARTBEAT.md | 心跳任务 | 心跳触发时 |
| BOOT.md | 启动检查 | Gateway 重启时 |
| MEMORY.md | 长期记忆 | 仅私信会话开始 |
| memory/YYYY-MM-DD.md | 每日记忆 | 今天 + 昨天自动加载 |

---

## 二、职责管理

### 2.1 Agent 角色定位方法论

**文件分工模型：**

```
SOUL.md  = 风格层（WHO I AM）
AGENTS.md = 执行层（HOW I OPERATE）
TOOLS.md  = 环境层（WHERE I WORK）
MEMORY.md = 知识层（WHAT I KNOW）
```

**SOUL.md 撰写原则（官方最佳实践）：**
- 简洁：≤ 1,000 字，避免重复 AGENTS.md 内容
- 区分风格与规则：风格在 SOUL，规则在 AGENTS
- 包含硬边界：明确 Agent **不做什么**
- 人格要素：名字、emoji、交流语气、核心价值观

**AGENTS.md 撰写原则（Playbook 核心建议）：**
- "执行操作系统"：规则必须可验证、可执行
- 避免模糊表述：`"Be helpful"` → `"需要记忆时写入 memory/YYYY-MM-DD.md"`
- 保持精简：每次会话都读，长文件消耗 token 并导致模型忽略
- 包含工作流：接收任务 → 确认需求 → 执行 → 交付的标准模式
- 明确边界：只接收来自特定 Agent 的任务

---

### 2.2 职责边界清晰化方法论

墨灵当前 AGENTS.md 红线规范（参考实例）：
- 不带目标地收集信息
- 不确认需求就开始研究
- 交付无结构的"信息堆砌"
- 假装知道不确定的事情
- 在 workspace 里放密钥（用 SecretRef）

**边界建立模式：**
1. **角色边界**：`只接收墨染(main)与(code-dev)的研究任务`
2. **能力边界**：在 MEMORY.md 中明确列出 ✅/❌
3. **操作边界**：HEARTBEAT.md 限制心跳任务范围
4. **安全边界**：TOOLS.md 中不泄露凭证，用 `$ENV_VAR_NAME` 引用

---

### 2.3 多 Agent 协作模式

**Skill 优先级（从高到低）：**
```
skills/workspace-local/     ← 最高（workspace 私有 skill）
~/.openclaw/skills/        ← 托管 skill
内置 bundled skills        ← 最低
```

**协作场景：**
- 主 agent → subagent：任务下发 + skill 指定 + 报告路径告知
- 墨灵实践：`skills=["in-depth-research"]` 显式指定，避免继承混乱
- `lightContext: false`：确保子 agent 完整方法论继承

**会话间通信工具：**
- `sessions_send` → 向其他 session 发送消息
- `sessions_spawn` → 后台子 agent 任务
- `council_start` → 多 agent 协作（git worktree 隔离）

---

## 三、记忆管理

### 3.1 MEMORY.md 内容组织方法论

**三层记忆架构：**

| 记忆类型 | 文件 | 生命周期 | 加载时机 |
|---|---|---|---|
| 身份与定位 | SOUL.md | 持久 | 每次会话 |
| 长期知识 | MEMORY.md | 持久 | 仅私信会话 |
| 每日上下文 | memory/YYYY-MM-DD.md | 日 | 今天 + 昨天自动加载 |
| 梦境提升 | DREAMS.md | 审查用 | 人工审查 |

**MEMORY.md 撰写规范（墨灵实践）：**
```markdown
## 核心定位
- [角色一句话描述]

## 能力边界
- ✅ [能做的事]
- ❌ [不能/不该做的事]

## 关键方法
- [核心方法论或流程]

## 相关资源
- [资源路径/链接]
```

**重要原则：**
- 决策、偏好、持久事实 → MEMORY.md
- 日间上下文、临时观察 → memory/YYYY-MM-DD.md
- "如果想让 agent 记住某事"：直接告诉它，agent 会写入合适文件

---

### 3.2 长期 vs 短期会话记忆

```
会话内记忆（RAM）
  └─ 每次对话回合的上下文窗口
  └─ compaction 时自动摘要（默认触发内存刷新）

磁盘持久记忆（workspace 文件）
  ├─ memory/YYYY-MM-DD.md   ← 每日笔记（短期）
  └─ MEMORY.md              ← 长期记忆（持久）
```

**自动内存刷新机制：**
- OpenClaw 在 compaction（会话压缩）前自动运行内存刷新
- 将重要上下文保存到 memory 文件，防止摘要丢失
- 墨灵 AGENTS.md 已将此行为显式写入规则

**Dreaming（可选后台提升）：**
- 将短期信号收集 → 打分 → 提升符合条件的条目到 MEMORY.md
- 保持 MEMORY.md 高信噪比
- 输出 DREAMS.md 供人工审查

---

### 3.3 memory_store 使用时机

**工具分层：**

| 工具 | 用途 | 触发场景 |
|---|---|---|
| `memory_store` | 写入结构化记忆到 LanceDB | 偏好、事实、决策、重要发现 |
| `memory_search` | 混合搜索（向量 + 关键词）| 召回历史记忆 |
| `memory_get` | 按 ID 或路径读取 | 特定记忆条目读取 |
| `memory_update` | 更新已有记忆 | 修正过时信息 |
| `memory_forget` | 删除记忆 | 隐私或过时条目清理 |

**最佳实践：**
- 偏好/决策/事实 → `memory_store`
- 日常研究笔记 → 写入 `memory/YYYY-MM-DD.md`（更可审计）
- 复杂知识体系 → `memory-wiki` 插件（wiki 结构化知识）
- 混合搜索支持语义召回（OpenAI/Gemini/Voyage/Mistral API key 自动启用）

---

## 四、学习与迭代

### 4.1 .learnings/ 目录用法

基于 OpenClaw 官方 `self-improving-agent` skill 的规范：

```
.learnings/
├── LEARNINGS.md          # 修正、洞察、知识盲区、最佳实践
├── ERRORS.md             # 命令失败、集成错误
└── FEATURE_REQUESTS.md   # 用户请求的功能
```

**触发场景对照表：**

| 情况 | 目标文件 | 类别 |
|---|---|---|
| 用户纠正你 | LEARNINGS.md | correction |
| 命令/操作失败 | ERRORS.md | - |
| API/外部工具失败 | ERRORS.md | - |
| 用户请求缺失功能 | FEATURE_REQUESTS.md | - |
| 知识过时/错误 | LEARNINGS.md | knowledge_gap |
| 发现更优方法 | LEARNINGS.md | best_practice |
| 模式简化/强化 | LEARNINGS.md | simplify-and-harden |

**晋升规则（关键）：**

| 学习类型 | 晋升目标 | 示例 |
|---|---|---|
| 行为/风格规则 | SOUL.md | "要简洁，避免免责声明" |
| 工作流/流程改进 | AGENTS.md | "复杂任务用 subagent" |
| 工具使用坑 | TOOLS.md | "git push 需先配置 auth" |
| 项目知识 | MEMORY.md | 团队规范、关键决策 |

**状态管理：** `pending` → `in_progress` → `resolved` / `promoted` / `wont_fix`

---

### 4.2 从错误中学习的元方法

**模式：`错误 → 记录 → 诊断 → 修复 → 晋升`**

1. **错误发生时**：记录到 ERRORS.md（含命令、错误信息、上下文），不泄露 secrets/full transcripts
2. **诊断类型**：文档缺失 → 晋升；缺少自动化 → 晋升到 AGENTS.md；架构问题 → tech debt 记录
3. **复现性判断**：可复现 → 找出根因；不可复现 → 记录降级处理
4. **晋升触发条件**：同一错误出现 2 次以上 / 影响多个文件 / 新成员应该知道

---

### 4.3 SELF_IMPROVEMENT_REMINDER 实践

**关键要点：**
- SELF_IMPROVEMENT_REMINDER 是**触发器**（写在 bootstrap 文件末尾），不是独立文件
- 每次任务结束后主动评估是否需要记录
- 避免"积累了很多 learn 但从不晋升"的空转
- 晋升是保持 agent 持续进化的唯一有效方式

---

## 五、实践元方法总结

### 元方法 1：Workspace 文件分层

- **核心原理**：bootstrap 文件按加载频率和生命周期分层，不同层级解决不同问题
- **具体操作**：SOUL.md → 人格风格；AGENTS.md → 操作规则；MEMORY.md → 长期知识；memory/ → 每日上下文；skills/ → 可执行技能模块
- **适用场景**：所有 OpenClaw Agent 初始化
- **模板**：
```markdown
# SOUL.md
## 我是谁（1-2句）
## 核心价值观（3-5条）
## 底线（3-5条，禁止行为）

# AGENTS.md
## 红线（必须遵守）
## Session 启动步骤
## 核心职责
## 工作流程
## 与伙伴的关系
```

---

### 元方法 2：Bootstrap 文件大小控制

- **核心原理**：文件大小直接影响 token 消耗和模型遵从度
- **具体操作**：AGENTS.md ≤ 5,000 字，SOUL.md ≤ 1,000 字；超大内容外置；在 bootstrap 文件中引用外置文件路径
- **适用场景**：长期迭代后 workspace 膨胀时
- **判断标准**：如果模型开始"忽略"某些规则，首先检查文件是否过大

---

### 元方法 3：记忆分层与晋升

- **核心原理**：短期记忆自动积累，长期记忆保持高质量（信噪比）
- **具体操作**：日间笔记 → memory/YYYY-MM-DD.md；持久决策 → MEMORY.md；定期晋升：将重复 daily notes 精华合并到 MEMORY.md
- **晋升标准**：同一知识被记录 3 次以上 → 晋升到 MEMORY.md

---

### 元方法 4：Learnings 闭环管理

- **核心原理**：错误和学习不被遗忘的唯一方式是结构化记录 + 明确晋升
- **具体操作**：任务结束 → 评估 SELF_IMPROVEMENT_REMINDER → 记录到 .learnings/ → pending 条目定期 review → 晋升路径：learnings → AGENTS.md/SOUL.md/TOOLS.md/MEMORY.md
- **晋升触发**：同一 pattern 出现 2 次 / 影响多文件 / 新成员应知

---

### 元方法 5：报告双文件交付

- **核心原理**：原始数据（md）与可视化（HTML）分离，确保可审计性和可读性
- **具体操作**：md 文件含完整方法论+来源追踪；HTML 文件结构化呈现+置信度；统一命名+统一路径
- **格式模板**：
```markdown
🔬 DEEP RESEARCH: [主题]
⚡ 一句话结论
📊 置信度：高/中/低 [原因]
🔍 核心发现
⚠️ 局限性
📚 来源（附可信度评估）
```

---

### 元方法 6：Symlink 隔离策略

- **核心原理**：workspace 是单一目录，用符号链接扩展存储和引用外部目录
- **具体操作**：大型报告目录 → 符号链接到 research/；projects/ → 符号链接；避免在 workspace 根目录直接创建大型文件
- **适用场景**：避免 workspace 单目录膨胀，便于全局 backup

---

## 六、数据来源

| 来源 | 内容 | 可信度 |
|---|---|---|
| docs.openclaw.ai/concepts/agent-workspace | 官方 workspace 架构文档 | ⭐⭐⭐⭐⭐ |
| docs.openclaw.ai/zh-CN/concepts/memory | 官方记忆系统文档 | ⭐⭐⭐⭐⭐ |
| docs.openclaw.ai/zh-CN/concepts/memory-search | 记忆搜索机制 | ⭐⭐⭐⭐⭐ |
| github.com/openclaw/skills (self-improving-agent) | 自我改进 skill 规范 | ⭐⭐⭐⭐⭐ |
| www.openclawplaybook.ai/blog/ | Playbook 实践指南 | ⭐⭐⭐⭐ |
| github.com/openclaw/openclaw | 源码文档 | ⭐⭐⭐⭐ |
| clawhub.ai | ClawHub skill 生态 | ⭐⭐⭐ |
| Reddit r/openclaw | 社区经验（需交叉验证） | ⭐⭐⭐ |

---

## 七、墨灵现状评估与改进建议

### 现状
- ✅ Bootstrap 文件结构完整（AGENTS.md、SOUL.md、TOOLS.md、IDENTITY.md、USER.md、HEARTBEAT.md）
- ✅ 记忆系统运行中（MEMORY.md + memory/ 目录）
- ✅ .learnings/ 目录已建立并有实际条目
- ✅ research/ 目录使用符号链接
- ✅ skills/ 目录包含多个 skill
- ⚠️ 根目录有直接放置的 .md 报告文件（应全部移入 research/）
- ⚠️ BOOTSTRAP.md 状态未知（应确认是否完成并删除）

### 改进建议
1. **清理根目录**：将根目录的 `.md` 报告文件移入 `research/` 子目录
2. **BOOTSTRAP.md 处理**：确认首次仪式完成后应删除或标记
3. **.learnings/ 定期 review**：每月 review 一次 pending 条目，执行晋升或关闭
4. **MEMORY.md 更新**：随着经验积累，定期将 .learnings 条目晋升

---

*报告完成 | 墨灵 🔍 | 2026-04-18*
