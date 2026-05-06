# Claude Code 代码修复与开发最佳流程研究报告

> 研究日期：2026-04-14
> 信息来源：Claude Code 官方文档 (code.claude.com)、GitHub、Reddit、社区博客

---

## 核心发现：推荐的标准开发工作流

Claude Code 官方推荐的工作流是 **「探索 → 计划 → 实施 → 验证 → 精简」** 五阶段流程，核心理念是**代理式开发（agentic development）**：你描述需求，Claude 负责探索、计划和实现，而非你写代码让 Claude 审查。

---

## 一、标准开发工作流（官方推荐）

### 阶段 1：探索（Explore）

**目的**：理解代码库，避免解决错误的问题。

**推荐操作**：
```bash
# 进入 Plan Mode 进行只读探索
claude --permission-mode plan
```

```text
give me an overview of this codebase
explain the main architecture patterns used here
trace the login process from front-end to database
```

**最佳实践**：
- 从宽泛问题开始，逐步深入特定区域
- 使用 `@/path/to/file` 引用具体文件
- 使用 `Ctrl+O` 开启 verbose 模式查看 Claude 的思考过程
- 用 `/init` 自动生成 CLAUDE.md 脚手架

**工具使用顺序**：`Read` → `Glob` → `Grep`（只读优先）

---

### 阶段 2：计划（Plan）

**目的**：在动手之前明确方向，减少上下文消耗。

**推荐操作**：
```bash
# 在 Plan Mode 中请求详细实现计划
claude --permission-mode plan

# 示例：规划复杂重构
I need to refactor our authentication system to use OAuth2. Create a detailed migration plan.

# 细化计划
What about backward compatibility?
How should we handle database migration?
```

**关键技巧**：
- 按 `Ctrl+G` 在文本编辑器中直接编辑 Claude 的计划
- 使用 `/plan` 前缀单次提示进入计划模式
- 计划接受后可选择：自动执行 / 手动逐个审批 / 继续细化

**何时跳过**：如果改动能用一句话描述（如修 typo、加日志），直接做，无需计划。

---

### 阶段 3：实施（Implement）

**目的**：执行计划，编写代码。

**推荐操作**：
```bash
# 从 Plan Mode 切换回 Normal Mode
Shift+Tab  # 循环切换权限模式
```

```text
implement the OAuth flow from your plan.
write tests for the callback handler, run the test suite and fix any failures.
```

**关键原则**：
- **给 Claude 验证手段**：提供测试命令、截图、预期输出，让 Claude 能自我检查
- 每次修改后运行测试，而非最后一次性验证
- 用小步增量修改，避免大范围重构后无法定位问题

---

### 阶段 4：测试验证（Test）

**推荐操作**：
```text
find functions in NotificationsService.swift that are not covered by tests
add tests for the notification service
add test cases for edge conditions
run the new tests and fix any failures
```

**最佳实践**：
- 让 Claude 分析现有测试文件以匹配项目风格
- 要求 Claude 识别边界情况（错误条件、边界值、意外输入）
- 同时运行 linter + 测试：`npm run lint && npm test`

---

### 阶段 5：精简（Compact/Refactor）

**推荐操作**：
```text
find deprecated API usage in our codebase
suggest how to refactor utils.js to use modern JavaScript features
refactor utils.js to use ES2024 features while maintaining the same behavior
run tests for the refactored code
```

**最佳实践**：
- 小的、可测试的增量重构
- 请求保持向后兼容性
- 要求 Claude 解释现代方法的优势

---

## 二、权限模式选择（--permission-mode）

| 模式 | 描述 | 适用场景 |
|:---|:---|:---|
| `default` | 标准模式，首次使用时请求权限 | 起步阶段、敏感操作 |
| `acceptEdits` | 自动接受文件编辑和常见文件系统命令 | 你在审查代码、需要快速迭代 |
| `plan` | 只读模式，只能分析不能修改 | 探索代码库、规划复杂变更 |
| `auto` | 全部自动执行，带后台安全检查 | 长任务、减少提示疲劳（需 v2.1.83+） |
| `dontAsk` | 仅预批准工具可运行 | CI 脚本、锁定环境 |
| `bypassPermissions` | 跳过所有检查（除保护路径） | **仅限隔离容器/VM** |

### CLI 切换方式

```bash
# 启动时指定
claude --permission-mode plan
claude --permission-mode acceptEdits

# 会话中切换
Shift+Tab  # 循环: default → acceptEdits → plan

# 配置默认模式（~/.claude/settings.json）
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

### 危险操作权限管理

```json
// settings.json - 白名单模式
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git commit *)",
      "Bash(git * main)"
    ],
    "deny": [
      "Bash(git push *)",
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}
```

**Bash 权限注意事项**：
- 规则按优先级匹配：`deny → ask → allow`
- 通配符 `*` 灵活但脆弱，不应用于 URL 过滤
- 复合命令（如 `git status && npm test`）会为每个子命令生成独立规则
- 环境运行器（`devbox run`, `mise exec`, `npx` 等）不自动剥离，需写具体规则

---

## 三、工具使用最佳实践

### 工具使用顺序

1. **先 Read，后 Edit**：先理解代码再修改
2. **用 `@` 引用文件**：`Explain @src/auth/login.js` 比"解释登录模块"更精确
3. **给验证手段**：告诉 Claude 如何验证成功（测试命令、截图对比）
4. **描述症状而非解决方案**：`"build fails with error X, fix the root cause"` 优于 `"remove the ts-ignore"`

### 核心原则：上下文窗口是稀缺资源

官方明确指出：LLM 性能随上下文窗口填充而下降。最重要的资源管理策略：

| 策略 | 操作 |
|:---|:---|
| 用 `/rename` 尽早命名会话 | 便于后续恢复 |
| 用 `@` 精确引用而非模糊描述 | 减少 token 消耗 |
| 小步修改，分次提交 | 避免长会话丢失上下文 |
| 用 `Ctrl+O` 切换 verbose 模式 | 按需查看思考过程 |

### 效率技巧

```bash
# 快速分析（无需交互）
claude --permission-mode plan -p "Analyze auth system and suggest improvements"

# 带验证的快速修复
echo "npm test error output" | claude "fix the failing test"
```

---

## 四、Session 生命周期管理

### 会话创建 vs 复用

| 场景 | 建议 |
|:---|:---|
| 新任务/新功能 | 创建新会话 |
| 同一功能的后续迭代 | 复用并用 `/rename` 重命名 |
| 探索代码库 | Plan Mode 新会话 |
| 从 PR 恢复 | `claude --from-pr <number>` |
| 快速单次查询 | `claude -p "query"`（headless） |

### Session Fork（实验分支）

当需要尝试不同方案但不破坏现有对话历史时：

```bash
# 创建实验分支
claude --fork-session

# 或在会话中
/fork  # 创建当前会话的独立副本
```

**典型场景**：
- 当前会话上下文已满，需要轻装探索
- 想尝试 A/B 两种实现方案
- 实验性重构，不想污染主分支

### Session Pause/Resume

```bash
# 恢复最近的会话
claude --continue

# 按名称恢复
claude --resume auth-refactor

# 按 ID 恢复（headless 或 SDK 创建的会话）
claude --resume <session-id>
```

**会话选择器快捷键**（`/resume` 后）：

| 快捷键 | 操作 |
|:---|:---|
| `↑/↓` | 导航会话 |
| `P` | 预览会话内容 |
| `R` | 重命名会话 |
| `A` | 切换所有项目 |
| `/` | 搜索过滤 |

### 止损策略（防止会话失控）

1. **提前命名**：`/rename task-name` 便于定位
2. **小步提交**：每次完成一个小功能后提交，避免长会话崩溃后无法恢复
3. **用 Fork 做实验**：不确定的改动先 fork 再尝试
4. **用 `--max-turns` 限制**：限制最大轮次防止无限循环

```bash
# 限制最大轮次和预算
claude --max-turns 50 --max-budget-usd 5.00 "task"
```

---

## 五、工具权限配置（--allowed-tools / --disallowed-tools）

### 白名单模式推荐配置

```bash
# 仅允许读和搜索工具（高度安全）
claude --allowed-tools Read,Grep,Glob,Bash

# 允许编辑但禁止危险命令
claude --allowed-tools Read,Grep,Glob,Bash,Edit,Write \
  --disallowed-tools Bash(rm -rf *),Bash(sudo *),Bash(docker rm *)
```

### 推荐实践

| 场景 | 推荐配置 |
|:---|:---|
| 代码审查 | `--allowed-tools Read,Grep,Glob` |
| 日常开发 | `--allowed-tools Read,Grep,Glob,Bash,Edit,Write` |
| CI/自动化脚本 | `--permission-mode dontAsk` + 严格 allowlist |
| 隔离实验 | `--permission-mode bypassPermissions` |

### 预算控制

```bash
# 设置最大美元预算和最大轮次
claude --max-budget-usd 10.00 --max-turns 100 "task"
```

---

## 六、Subagents（子代理）使用

### 内置 Subagent

| Subagent | 模型 | 工具 | 用途 |
|:---|:---|:---|:---|
| Explore | Haiku | 只读 | 快速代码库探索 |
| Plan | 继承主会话 | 只读 | 计划模式中的研究 |
| General-purpose | 继承主会话 | 全部 | 复杂多步骤任务 |

### 自定义 Subagent 示例

```bash
# 通过 /agents 命令创建
/agents  # 打开交互式界面

# 或通过 CLI 定义（会话级）
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer for security and quality",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  }
}'
```

### 多 Subagent 协作（顺序）

```text
use the code-reviewer subagent to check the auth module
have the debugger subagent investigate why users cannot log in
```

### Subagent 文件存储位置

| 位置 | 范围 | 优先级 |
|:---|:---|:---|
| Managed settings | 组织级 | 1（最高） |
| `--agents` CLI flag | 当前会话 | 2 |
| `.claude/agents/` | 项目 | 3 |
| `~/.claude/agents/` | 用户 | 4 |
| 插件目录 | 插件启用范围 | 5（最低） |

---

## 七、OpenClaw 环境集成

### 通过 CLI 调用 Claude Code

```bash
# 基本调用
claude "fix the login bug"

# 指定工作目录
claude -d /path/to/project "implement feature X"

# 权限模式
claude --permission-mode plan -d /path/to/project "analyze auth system"

# 流式输出（适合脚本）
claude --continue --print "fix the failing test"
```

### 注意事项

- Claude Code 会话存储在项目目录的 `.claude/` 中
- 用 `--add-dir` 添加额外目录（仅授予文件访问，不含配置）
- OpenClaw 环境中需确保 `$DISPLAY` 正确配置（如有 UI 需求）
- 建议通过 `openclaw mcp` 确认 Claude Code MCP 服务状态

### 与 OpenClaw 的工作分配

建议工作分配：
- **OpenClaw 主会话**：规划、决策、外部通信、记忆管理
- **Claude Code**：需要大量代码探索、修改、测试的开发任务
- **两者协作**：OpenClaw 指挥方向，Claude Code 执行代码

---

## 八、常见陷阱

### 1. 上下文耗尽
**问题**：长会话后期 Claude 开始"遗忘"早期指令。
**解决**：小步提交、定期开新会话、用 `/rename` 命名会话便于恢复。

### 2. 修复错误的问题
**问题**：直接让 Claude 写代码，绕过了探索和计划阶段。
**解决**：用 Plan Mode 先理解代码，再制定计划，最后实施。

### 3. 缺乏验证手段
**问题**：告诉 Claude "make it work"，Claude 无法自我验证。
**解决**：提供测试命令、预期输出、截图对比，让 Claude 有反馈循环。

### 4. 过度计划
**问题**：修 typo 也开 Plan Mode。
**解决**：能用一句话描述的改动，直接做。计划留给复杂/多文件变更。

### 5. 权限模式选错
**问题**：`bypassPermissions` 在主环境使用导致意外修改。
**解决**：仅在隔离容器/VM 中使用 `bypassPermissions`。

### 6. 会话失控（死循环）
**问题**：Claude 陷入反复修改同一文件的循环。
**解决**：
- 用 `--max-turns` 限制轮次
- 用 `Ctrl+C` 中断并 `/resume` 恢复
- 用 `--fork-session` 创建实验分支

### 7. 权限规则误配
**问题**：`Bash(curl *)` 规则无法限制 URL。
**解决**：使用 `WebFetch(domain:example.com)` 权限而非 Bash URL 过滤。

---

## 九、快速参考命令卡

```bash
# 启动
claude                          # 普通会话
claude --permission-mode plan   # Plan Mode 探索
claude -d /path/to/project      # 指定目录
claude -n "session-name"        # 命名会话

# 会话管理
claude --continue               # 继续最近会话
claude --resume <name-or-id>    # 按名称恢复
claude --from-pr <number>       # 从 PR 恢复
claude --fork-session           # 创建实验分支

# 工具权限
claude --allowed-tools Read,Grep,Glob,Bash,Edit
claude --disallowed-tools Bash(rm *)
claude --max-budget-usd 5.00
claude --max-turns 50

# Subagent
claude --agents '{"reviewer": {"tools": ["Read", "Grep"], "model": "sonnet"}}'

# 模式切换（会话中）
Shift+Tab                       # 循环切换权限模式
Ctrl+G                          # 在编辑器中编辑计划
Ctrl+O                          # 切换 verbose 模式
```

---

## 十、参考资料

- [Claude Code Common Workflows](https://code.claude.com/docs/en/common-workflows)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code Permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code Permission Modes](https://code.claude.com/docs/en/permission-modes)
- [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference)
- [GitHub: shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows)
- [GitHub: wshobson/agents](https://github.com/wshobson/agents)
