# Vibecoding 下的 CLAUDE.md 最佳模板研究

**🔬 DEEP RESEARCH: Vibecoding 场景下的 CLAUDE.md 最佳模板**

**时间：2026-04-18 | 研究深度：标准 | 置信度：高**

---

## ⚡ 一句话结论

Vibecoding 的 CLAUDE.md 不是项目文档，而是**AI 行为契约**——用最精简的指令纠正 AI 在编码中最常见的越界行为，平衡"直觉发挥"与"必要约束"。

---

## 📊 置信度：高

**原因：** 核心模板来源为 2026 年 4 月 5800+ Stars 的 viral GitHub repo（Karpathy 原则），辅以官方文档、多个社区模板、真实项目经验报告，来源权威且时效新（3 天内）。

---

## 🔍 核心发现

### 1. Vibecoding 是什么

**定义（Andrej Karpathy 2025 年初提出）：**
> Vibecoding = 用自然语言表达意图，AI 将其转化为可执行代码的编程范式。

**核心理念：**
- AI 是**协作者**，不是代码生成器
- 从"我要写代码" → "我要描述我要什么"
- 快速迭代，不追求架构一步到位

**与崔统编程的区别：**

| 维度 | 崔统编程 | Vibecoding |
|------|----------|------------|
| 入口 | 需求文档 → 设计 → 编码 | 自然语言意图 → AI 生成 → 迭代 |
| 方向 | 自上而下（规划驱动） | 自下而上（直觉驱动） |
| 速度 | 慢但可控 | 快但需边界约束 |
| AI 角色 | 辅助工具 | 协作伙伴 |
| 风险 | 需求变更成本高 | AI 越界风险高 |

**为什么需要特殊的 CLAUDE.md：**
AI 在 vibecoding 中被给予更大的自由度，但自由意味着更高的越界风险。CLAUDE.md 作为"行为宪法"，需要同时：
1. **约束** AI 不要过度工程化
2. **赋能** AI 自由探索和快速迭代
3. **保护** 人类在关键节点保持控制

---

### 2. 官方 CLAUDE.md 指南

**关键原则（来自 Claude Code 官方文档）：**

- **150-200 条指令上限**：超过后合规性急剧下降（系统提示已占用约 50 条）
- **CLAUDE.md 是建议性的**：Claude 大约 80% 遵循度
- **确定性的事交给 Hooks**：格式化、安全检查等用 hooks，CLAUDE.md 专注射行指导
- **分层加载**：home (~/.claude/CLAUDE.md) → project root → directory-specific
- **`<important if="...">` 标签**：文件变长时用此标签标注关键规则，防止被忽略

**推荐结构（官方 + 社区收敛）：**
1. Project Overview（项目概述）
2. Tech Stack & Commands（技术栈和命令）
3. Coding Conventions（编码约定）
4. Critical Rules（关键规则）
5. Architecture/Patterns（架构模式，可选）

---

### 3. 社区最佳实践

**Karpathy CLAUDE.md（最 viral，2026-04-13）：**
- 5800+ Stars 单日，GitHub Trending 第二
- 4 条核心原则：**先思考再编码 → 简洁优先 → 手术刀式变更 → 目标驱动执行**
- 全部内容 < 200 行，完全可执行
- 核心洞察：LLM 在编码中的最大问题不是能力不足，而是**隐性假设**和**过度工程化**

**其他参考来源：**
- `chrishayuk/vibe-coding-templates`：Python 项目模板，强调 bootstrap 流程和工具链（uv、pytest、ruff）
- `shanraisshan/claude-code-best-practice`：覆盖 subagent、hooks、MCP、skills 的完整体系，`<important if>` 标签来自此处
- `RanTheBuilder` 经验报告：CLAUDE.md 应 < 200 行，用 `import` 链接 skills，BMAD vs plan mode 决定项目复杂度

**社区共识：**
- 少即是多：不要把 CLAUDE.md 写成项目百科全书
- 行为导向：关注 AI *如何工作*，而非项目 *包含什么*
- 可执行验证：每条规则应有可验证的检查点

---

## 两套 CLAUDE.md 模板

### 模板A：Vibe Sprint（氛围冲刺版）

**定位**：轻量级，适合快速启动的 vibecoding 项目。
**行数目标**：< 100 行

\`\`\`markdown
# 🌀 {项目名称}

## 我是谁
- 开发者：{你的名字}
- 项目类型：{Web应用/API/脚本/CLI/...}
- 目标用户：{谁会用这个}

## 我们怎么合作
- 告诉我**要什么**，不是**怎么写**
- 有疑问先说，别猜
- 复杂功能先列出选项再动手
- 我做验证，你来检查结果

## 铁律（违反就停）
- ❌ 不写我没要求的代码
- ❌ 不重构没坏的地方
- ❌ 不在 diff 里改我改动范围以外的东西
- ❌ 不 commit 任何密钥
- ✅ 改动超过 50 行，先解释再动手
- ✅ 每次生成代码后，说清楚验证方法

## 技术栈
- 语言/框架：{如 Python + FastAPI}
- 包管理：{如 uv / npm}
- 测试：{如 pytest}
- 代码质量：{如 ruff, ESLint}

## 常用命令
| 操作 | 命令 |
|------|------|
| 安装依赖 | {uv sync / npm install} |
| 运行 | {uv run dev / npm start} |
| 测试 | {uv run pytest / npm test} |
| 代码检查 | {uv run ruff check / npm run lint} |

## 验证标准
任务完成后，必须报告：
1. ✅ 做了什么
2. 🧪 怎么验证（具体命令或步骤）
3. ⚠️ 还有什么不确定的
\`\`\`

---

### 模板B：Vibe Lab（深度协作版）

**定位**：完整版，适合多文件、多人参与、需要架构约束的项目。
**行数目标**：< 250 行

\`\`\`markdown
# 🌀 {项目名称} — Vibe Lab

## 项目概述
- **开发者**：{你的名字}
- **项目类型**：{Web 应用 / API 服务 / CLI 工具 / 数据管道 / ...}
- **核心功能**：{1-2 句话描述这个项目做什么}
- **目标用户**：{谁会使用这个项目}

---

## 🤝 Vibecoding 工作流

### 我的工作方式
- 我用自然语言描述需求，你用代码回应
- 复杂任务 → 先列出方案选项，再选一个执行
- 大改动（涉及多个文件或架构调整）→ 先用 `/plan` 模式
- 随时可以问我：这个方向对吗？

### 你的行动原则
1. **先说后做**：实施方案前先陈述你的假设
2. **简洁为王**：解决当前问题即可，不要过度设计
3. **手术刀变更**：只碰需要碰的文件，不要美化周边
4. **目标验证**：每个任务交付时必须有验证方法
5. **不确定性上报**：遇到不清楚的，立即问，不要猜

---

## 🚫 铁律（违反立即停手）

<important if="editing existing files">
- ❌ 不改我改动范围以外的文件
- ❌ 不重新格式化我没改动的代码
- ❌ 不删 pre-existing dead code（除非我说）
- ❌ 不在 PR 里混入风格重构
</important>

<important if="writing new code">
- ❌ 不写 speculative code（没有请求的功能/配置/抽象）
- ❌ 不引入我没有的依赖
- ❌ 不在代码里 hardcode 密钥（用环境变量）
</important>

<important if="any task">
- ✅ 超过 50 行的改动 → 先解释再执行
- ✅ 每次交付 → 说明验证步骤
- ✅ 发现更好的方案 → 说出来，等我确认
- ✅ 发现安全风险 → 立即上报
</important>

---

## 🏗 技术栈与架构

### 核心依赖
- **运行时**：{如 Python 3.12 / Node 20}
- **框架**：{如 FastAPI / Next.js}
- **数据库**：{如 PostgreSQL / SQLite}
- **包管理**：{uv / npm / pnpm}

### 项目结构
\`\`\`
{src/}           # 源代码
{tests/}         # 测试文件
{docs/}          # 文档
{scripts/}       # 辅助脚本
{.claude/}       # AI 配置
\`\`\`

### 关键架构约束
- {如：所有 API 路由在 `app/routes/`}
- {如：数据库操作通过 `app/repositories/` 层}
- {如：所有配置通过 `config.yaml` 而非 hardcode}

---

## 🧪 质量保障

### 测试要求
- 新功能 → 必须有测试用例
- Bug 修复 → 必须先写复现测试
- 运行命令：`{uv run pytest / npm test}`

### 代码质量
- Linter：`{uv run ruff check / npm run lint}`
- Formatter：`{uv run ruff format / npm run format}`
- Type check：`{uv run mypy src/ / npm run type-check}`
- 提交前必须通过以上所有检查

---

## ⚡ 常用命令速查

| 操作 | 命令 |
|------|------|
| 安装依赖 | `uv sync` / `npm install` |
| 开发模式 | `uv run dev` / `npm run dev` |
| 运行测试 | `uv run pytest` / `npm test` |
| 代码检查 | `uv run ruff check .` / `npm run lint` |
| 代码格式化 | `uv run ruff format .` / `npm run format` |
| 类型检查 | `uv run mypy src/` / `npm run type-check` |
| 构建 | `uv build` / `npm run build` |
| 全量 QA | `make qa` / `npm run qa` |

---

## 📋 Git 提交规范

- 使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式
- 格式：`type(scope): description`
- 示例：`feat(auth): add OAuth2 login`
- 提交前必须：`{uv run ruff check . && uv run pytest}`

---

## 🔗 关联资源

- Skills：{如 @frontend-design, @seo-analysis}
- MCP Servers：{如 GitHub, Chrome, Playwright}
- 文档：`docs/` 目录下有详细指南

---

## ✅ 交付检查清单

每次完成任务后，确认：
- [ ] 描述：做了什么
- [ ] 验证：用什么命令/步骤确认它工作
- [ ] 风险：还有什么不确定的地方
- [ ] 后续：下一步建议做什么（可选）
\`\`\`

---

## 设计原理

### 为什么这样设计

**Template A（Vibe Sprint）：**
1. **极简指令集**：只保留最核心的合作方式和铁律，开发者能快速设置
2. **表格化命令速查**：降低记住命令的成本，减少"怎么运行"的循环提问
3. **交付报告模板**：内置验证报告结构，解决 AI"做完就说成功"的问题
4. **无门槛导入**：任何项目复制粘贴即可使用，无额外配置

**Template B（Vibe Lab）：**
1. **`<important if>` 标签**：条件化规则，避免规则被稀释（文件增长时 Claude 会忽略中间部分）
2. **行为原则层 + 铁律层分离**：原则是指导方针，铁律是硬约束，优先级清晰
3. **质量保障内置**：测试 + linting + formatting 不只是列出来，而是与交付检查清单联动
4. **Git 规范**：减少 vibecoding 场景常见的"提交混乱"问题
5. **关联资源引用**：支持 Skills/MCP 扩展，不把 CLAUDE.md 做成百科全书

### 适用于哪些场景

| 场景 | 推荐模板 |
|------|----------|
| 快速原型/Hackathon | 模板A |
| 个人 side project | 模板A（熟悉后迁移 B） |
| MVP 产品开发 | 模板B |
| 多人协作项目 | 模板B |
| 需要安全合规的项目 | 模板B |
| 自动化/CI 场景 | 模板A（精简，去掉交付报告） |

---

## ⚠️ 局限性

- CLAUDE.md 遵循度约 80%，不能替代 hooks 和 CI 检查
- 模板需根据具体技术栈定制，以上为通用起点
- 200 行软上限需持续维护，避免文件膨胀

---

## 📚 来源

| # | 来源 | 可信度 | 说明 |
|---|------|--------|------|
| 1 | [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)（2026-04-13，5800+ Stars） | ⭐⭐⭐⭐⭐ | 核心模板来源，Karpathy 行为原则 |
| 2 | [chrishayuk/vibe-coding-templates](https://github.com/chrishayuk/vibe-coding-templates) | ⭐⭐⭐⭐ | Python vibecoding 项目模板参考 |
| 3 | [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)（2026-04，持续更新） | ⭐⭐⭐⭐⭐ | 完整 Claude Code 功能体系，`<important if>` 来源 |
| 4 | [RanTheBuilder - Claude Code Best Practices](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/)（2026-03-23） | ⭐⭐⭐⭐ | 真实项目经验，CLAUDE.md 结构建议 |
| 5 | [dev.to - Karpathy CLAUDE.md 分析](https://dev.to/max_quimby/karpathys-claudemd-template-5800-stars-and-what-it-does-4a09)（2026-04-15） | ⭐⭐⭐⭐ | 深度分析，含平台生态信号 |
| 6 | [IBM - What is Vibe Coding](https://www.ibm.com/think/topics/vibe-coding) | ⭐⭐⭐ | 崔统定义参考 |
| 7 | [dinanjana.medium - Mastering the Vibe](https://dinanjana.medium.com/mastering-the-vibe-claude-code-best-practices-that-actually-work-823371daf64c) | ⭐⭐⭐ | 社区实践视角 |
| 8 | [code.claude.com - Best Practices](https://code.claude.com/docs/en/best-practices) | ⭐⭐⭐⭐⭐ | 官方文档（间接引用） |

**数据时效性**：2026-04-13 ~ 2026-04-18，均为最新讨论。
