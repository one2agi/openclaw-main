**OpenClaw（龙虾）的“文档使用机制”** 是其 **Agent Runtime（代理运行时）** 的核心设计之一，官方称为 **Workspace Bootstrap + Context Injection（工作区引导 + 上下文注入）**。

它不是传统“读取文件”的方式，而是**在每次 Agent Loop（代理循环）启动时，由 Gateway/Context Engine 自动把特定 Markdown 文件的内容**“注入”到 LLM 的系统提示（system prompt）和上下文窗口里，让模型“一开始就知道自己是谁、该怎么做、记住什么”。

所有文档都存放在**单个 Agent Workspace**（默认路径 `~/.openclaw/workspace`，多 Agent 时每个 Agent 有独立 workspace），这是 Agent 的“家”和唯一工作目录。文档本身是纯 Markdown，用户可随时用编辑器修改，修改后下次 session 自动生效（部分支持热刷新）。

### 1. 核心文档定位与职责（Bootstrap 文件列表）

OpenClaw 在 session 启动/每轮推理前**固定注入**以下文件（可通过 `/context` 命令查看实际注入大小和截断情况）：

| 文档文件名          | 定位（是什么）                  | 主要职责                                                                 | 注入时机与特殊规则 |
|---------------------|--------------------------------|--------------------------------------------------------------------------|---------------------|
| **AGENTS.md**      | 操作手册 + “大脑操作系统”      | 定义启动流程、读取规则、行为守则、工具使用原则、记忆管理策略等（最像“宪法”） | 每次 session 必注；常包含“先读 SOUL.md + 今日记忆”的引导语句 |
| **SOUL.md**        | 个性与声音文件                 | 定义语气、价值观、边界、决策风格、角色定位（让 Agent “像一个人”）       | 每次普通 session 必注；影响输出风格最直接的文件 |
| **TOOLS.md**       | 环境专属工具笔记               | 记录本地特有配置（设备名、SSH 别名、偏好设置等）；补充 Skills 的个性化部分 | 每次 session 必注；与共享的 SKILL.md 互补 |
| **IDENTITY.md**    | 身份卡                         | Agent 名称、表情、emoji、简短自我介绍                                  | 每次 session 注入 |
| **USER.md**        | 用户画像                       | 你的偏好、称呼方式、背景信息等                                           | 每次 session 注入 |
| **MEMORY.md**      | 长期记忆（Long-term Memory）   | 持久事实、偏好、铁律、历史决策总结；“人脑式”长期记忆                    | 主会话（DM）才注入；群聊/子 Agent 不注入（防泄露） |
| **memory/YYYY-MM-DD.md** | 每日记忆日志                | 当天/最近几天的运行上下文、观察记录                                     | AGENTS.md 引导下按需读取（非自动全注入） |
| **HEARTBEAT.md**   | 主动任务/心跳模板              | 定时/后台任务的指令模板                                                  | 通常省略或按需 |

这些文件内容会被**截断处理**（单文件默认上限 `bootstrapMaxChars`，总上限 `bootstrapTotalMaxChars`），防止 token 爆炸；截断时会插入警告提示。

### 2. Skills（技能文档）—— 另一套并行机制

- 每个技能是一个文件夹，核心文件是 **SKILL.md**（含 YAML frontmatter + 详细指令）。
- **定位**：工具使用“教科书”，教 Agent **何时、何地、如何** 安全调用具体 tool。
- **职责**：提供约束、步骤、示例、最佳实践；Skills 是共享的（可从 ClawHub 安装），不含个人隐私。
- **注入方式**：与上面 bootstrap 文件不同——Skills 的**元数据**（名称、描述）固定注入系统提示，**完整指令**按需（on-demand）读取，避免上下文过大。
- 位置：`~/.openclaw/workspace/skills/<skill-name>/SKILL.md`（或插件内）。

### 3. 它们之间如何协调（完整流程）

1. **Session 启动 → Context Engine 组装**：
   - Gateway 收到消息 → Agent Runtime 触发 Agent Loop。
   - Context Engine 先读取 workspace 中的所有 bootstrap 文件，按固定顺序拼接成 “Project Context” 块，注入系统提示最前面。

2. **AGENTS.md 担任“指挥官”**：
   - 几乎所有模板的 AGENTS.md 都会明确写：
     - “先读 SOUL.md、USER.md、今日+昨日 memory/ 文件”
     - “MEMORY.md 只在主会话加载”
     - “Tools 按 SKILL.md 执行，环境细节看 TOOLS.md”
   - 模型在思考前就被要求遵守这些规则，实现“自我协调”。

3. **动态补充 + 记忆系统**：
   - 运行中 Agent 可通过 memory_search / file_read 等工具主动读取 daily memory 或 MEMORY.md。
   - Hooks（如 session-memory）自动把对话总结写回 memory/ 文件，形成闭环。
   - Context Engine 支持插件扩展（Context Engine plugins），可动态插入额外提示。

4. **安全与边界控制**：
   - MEMORY.md 故意**不在群聊/子 Agent**注入，防止隐私泄露。
   - 大文件自动截断 + 警告。
   - Skills 可配置权限过滤（environment / binary check）。

5. **可视化与调试**：
   - 命令 `/context` 可看到每份文件“原始大小 vs 实际注入大小”。
   - Dashboard 中可直接编辑所有 workspace 文件。

**一句话总结机制**：  
**AGENTS.md + SOUL.md 是“灵魂与规则”，MEMORY.md 是“经验”，TOOLS.md 是“本地配置”，SKILL.md 是“技能手册”** —— 它们通过 **Context Injection** 被统一打包成 LLM 每次思考的“初始大脑状态”，再由 AGENTS.md 里的引导语句让模型自己协调使用，形成一个自洽的“数字人格 + 记忆 + 能力”系统。
