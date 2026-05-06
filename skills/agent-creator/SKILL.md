---
name: agent-creator
description: Guide for creating new OpenClaw agents with proper workspace structure, identity files, configuration, and initial tuning. Use when faiz asks to create a new agent, add a bot, set up an agent's workspace, or tune an agent's documents.
---

# Agent Creator

Creates new OpenClaw agents with proper workspace structure, configuration, and initial tuning.

## When to Use

- faiz asks to create a new agent
- Adding a new Telegram bot to an existing agent
- Setting up an agent's workspace from scratch
- Tuning an agent's documents

---

## 官方核心文件最佳设计原则

> 以下是 OpenClaw 官方推荐的 agent 文件设计原则，必须严格遵守。

### 文件职责对照表

| 文件 | 官方用途 | 最佳实践 | 推荐长度 |
|------|---------|---------|---------|
| **SOUL.md** | 人格、语气、核心价值观、边界 | 只放性格、底线、价值观，不放流程 | **2-4KB，越短越好** |
| **AGENTS.md** | 操作系统指令、启动行为、内存规则、优先级、红线、安全边界 | "运营手册/SOP"，所有流程、规则、决策逻辑放这里 | **8-15KB** |
| **IDENTITY.md** | 代理名字、角色、emoji、vibe | 简单一句话 + emoji，让代理有"名片" | **1-2行** |
| **USER.md** | 用户信息（称呼、时区、偏好、工作背景） | 写得越具体越好，让代理"懂你" | 简洁 |
| **MEMORY.md** | 精选长期记忆（仅主/私密会话加载） | 定期用 heartbeat 审阅 daily log 并提炼到这里 | 定期维护 |
| **HEARTBEAT.md** | 心跳检查清单（30分钟一次） | 写成短 checklist，让代理主动但不打扰 | **极短** |
| **TOOLS.md** | 环境专属备注（相机名、SSH 别名、TTS 偏好等） | 只写本地特有配置，不重复技能定义 | **极短，纯笔记式** |

### 最重要设计原则

1. **职责分离**：
   - SOUL.md = "我是谁 + 底线"
   - AGENTS.md = "我怎么做事 + 流程"

2. **保持简短**：所有 bootstrap 文件太长会触发截断（默认单文件 20k 字符，总 150k）

3. **迭代进化**：让代理自己编辑这些文件，每次学到新东西就更新

4. **角色专属定制**：
   - Researcher 代理 → AGENTS.md 重点写搜索优先级、来源验证、输出格式
   - Coder 代理 → AGENTS.md 重点写代码规范、审核流程

5. **安全红线一定要写在 AGENTS.md 最前面（Red Lines 章节）**

### 避免常见坑

❌ 把流程写进 SOUL.md（会让人格文件变臃肿）
❌ TOOLS.md 写"可用工具列表"（那是 skills/ 的事）
❌ MEMORY.md 在群聊加载（只在私密会话加载）
❌ workspace 里放密钥（用 SecretRef）

---

## Creation Checklist

### Phase 1: Workspace Setup

```
~/.openclaw/workspace/agents/<agent-name>/
├── SOUL.md        # 人格定义（2-4KB）
├── IDENTITY.md    # 名字 + emoji（1-2行）
├── AGENTS.md      # 运营手册（8-15KB）
├── MEMORY.md      # 长期记忆
├── HEARTBEAT.md   # 心跳检查（极短）
├── TOOLS.md       # 环境备注（极短）
├── USER.md        # 用户信息
├── .learnings/    # 执行教训
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
├── memory/        # 项目记忆
│   └── projects/
└── skills/        # 专属 skills（可选）
```

### Phase 2: Create Identity Files

#### SOUL.md Template
```markdown
# SOUL.md — <Name>

**我是<名字>，<角色>。**

## 我是谁

- **名字**：<Name>（<Chinese>）
- **角色**：<Role>
- **上级**：<Superior>
- **Emoji**：<Emoji>

## 核心价值观

1. <Value 1>
2. <Value 2>
3. <Value 3>

## 底线

- <红线1>
- <红线2>
- <红线3>
```

#### IDENTITY.md Template
```markdown
# IDENTITY.md

- **名字**：<Name>
- **本质**：<Essence>
- **Emoji**：<Emoji>
```

#### AGENTS.md Template
```markdown
# AGENTS.md — <Name> 运营手册

## 红线（必须遵守）

- <红线1>
- <红线2>
- <红线3>
- 不在 workspace 里放密钥

## Session 启动

1. 读 SOUL.md
2. 读 MEMORY.md
3. 读 AGENTS.md

## 核心职责

<Description>

## 与<Superior>的关系

- <Relationship>

## 工作空间

- 主目录：`~/.openclaw/workspace/agents/<agent-name>/`
- 研究报告：`~/.openclaw/workspace/research/`
- 每日记忆：`~/.openclaw/workspace/memory/`
```

### Phase 3: OpenClaw Config

```bash
# 1. 创建 agent 配置
python3 -c "
import json

with open('~/.openclaw/openclaw.json') as f:
    d = json.load(f)

# Add agent
agents_list = d['agents']['list']
agents_list.append({
    'id': '<agent-id>',
    'workspace': '~/agents/<agent-name>',
    'model': 'minimax/minimax-2.7'
})

# Add Telegram account (if bot)
accounts = d['channels']['telegram']['accounts']
accounts['<account-id>'] = {
    'botToken': '<token>',
    'dmPolicy': 'allowlist',
    'allowFrom': ['7754385134']
}

# Add binding
bindings = d.get('bindings', [])
bindings.append({
    'match': {'channel': 'telegram', 'accountId': '<account-id>'},
    'agentId': '<agent-id>'
})

with open('~/.openclaw/openclaw.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
"

# 2. 重启网关
openclaw gateway restart
```

### Phase 4: Git Backup（官方强烈推荐）

```bash
cd ~/.openclaw/workspace/agents/<agent-name>
git init
git add AGENTS.md SOUL.md IDENTITY.md MEMORY.md memory/ skills/
git commit -m "Initial <agent-name> workspace"
```

### Phase 5: Copy Skills（可选）

```bash
# 复制相关 skills 到 agent workspace
mkdir -p ~/.openclaw/workspace/agents/<agent-name>/skills
cp -r ~/.openclaw/workspace/skills/<skill1> ~/.openclaw/workspace/agents/<agent-name>/skills/
```

### Phase 6: Link Research Projects（可选）

```bash
# 链接研究目录
ln -sf ~/.openclaw/workspace/research ~/.openclaw/workspace/agents/<agent-name>/research
```

---

## Agent 调教指南

创建完 agent 后，根据其角色进行调教。

### 调教原则

1. **先阅读官方最佳实践**（参考本文件第一节）
2. **根据 agent 角色定制配置**
3. **不要过度调教**：先让 agent 运行，根据反馈再调整
4. **保持精简**：所有 bootstrap 文件 <150KB 总计

### 调教检查清单

| 顺序 | 文件 | 检查点 |
|------|------|--------|
| ① | IDENTITY.md | 名字 + emoji，一句话角色 |
| ② | SOUL.md | 性格+底线+价值观，不放流程，2-4KB |
| ③ | AGENTS.md | 红线在最前面，核心职责，工作流程，8-15KB |
| ④ | MEMORY.md | 能力边界，关键结论，资源位置 |
| ⑤ | TOOLS.md | 仅本地环境配置 |
| ⑥ | HEARTBEAT.md | 极短 checklist |

### Skills 复制参考

| Agent 类型 | 需要复制的 skills |
|-----------|------------------|
| 研究类 | in-depth-research, market-research, multi-source-research, gemini-deep-research, reddit-readonly |
| 营销类 | marketing-framework |
| 代码类 | claude-code-master |

### 验证调教效果

通过 Telegram 测试 agent：
1. 能否正确介绍自己
2. 能否理解自己的角色
3. 能否正确使用配置的 skills

### 常见调教问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| Agent 不理解自己的角色 | SOUL.md 太模糊 | 明确写出角色定位 |
| Agent 流程混乱 | AGENTS.md 缺少流程定义 | 补充工作流程 |
| Agent 行为奇怪 | SOUL.md 混入了流程 | 分离到 AGENTS.md |
| Agent 丢失上下文 | bootstrap 文件太长 | 精简到限制内 |
