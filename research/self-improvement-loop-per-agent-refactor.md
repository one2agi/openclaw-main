# Self-Improvement-Loop Per-Agent 重构方案

> 生成时间：2026-04-23
> 目标：将 self-improvement-loop 从全局单实例改为全私有 per-agent 架构

---

## 一、目标架构

### 1.1 目录结构

```
~/.openclaw/
├── workspace/
│   ├── .learnings/                        ← 墨染（主 agent）私有
│   │   ├── LEARNINGS.md
│   │   ├── ERRORS.md
│   │   ├── FEATURE_REQUESTS.md
│   │   ├── .pending_notifications/
│   │   └── distill_output.json
│   │
│   ├── agents/
│   │   ├── 墨灵/
│   │   │   ├── SOUL.md                   ← 墨灵私有 persona
│   │   │   ├── AGENTS.md                 ← 墨灵私有规则
│   │   │   ├── .learnings/               ← 墨灵私有 learnings ✅已有
│   │   │   │   ├── LEARNINGS.md
│   │   │   │   ├── ERRORS.md
│   │   │   │   ├── FEATURE_REQUESTS.md
│   │   │   │   └── .pending_notifications/
│   │   │   └── scripts/                  ← 墨灵私有脚本（从模板初始化）
│   │   │
│   │   ├── 无极/
│   │   │   ├── SOUL.md
│   │   │   ├── AGENTS.md
│   │   │   ├── .learnings/
│   │   │   └── scripts/
│   │   │
│   │   └── CC/
│   │       ├── SOUL.md
│   │       ├── AGENTS.md
│   │       ├── .learnings/
│   │       └── scripts/
│   │
│   └── scripts/self-improvement/         ← 全局共享脚本模板（只读）
│       ├── distill.sh
│       ├── distill_json.py
│       ├── archive.sh
│       ├── write_notified.py
│       ├── setup_crons.py
│       ├── cron-payloads.json
│       └── agents-append.md
│
├── hooks/self-improvement/                ← 全局唯一 Hook（内部路由）
│   ├── handler.js                         ← 按 cwd 路由到对应 agent
│   └── HOOK.md
│
└── skills/                                ← 全局共享 skill（不变）
    ├── skill-creator/
    └── skill-improvement/
```

### 1.2 共享 vs 私有清单

| 内容 | 策略 | 说明 |
|------|------|------|
| handler.js | **全局共享，内路由** | 唯一 hook，通过 cwd 判断写入哪个 agent |
| 脚本模板（distill.sh 等） | **全局只读模板** | 每个 agent 初始化时复制一份到自己的 scripts/ |
| learnings 数据文件 | **全私有** | 每个 agent 读写自己的 .learnings/ |
| pending_notifications | **全私有** | 每个 agent 在自己的 .learnings/.pending_notifications/ |
| distill 输出 | **全私有** | 每个 agent 生成自己的 distill_output.json |
| cron jobs | **全私有** | job 名格式 `si.<agent>.<job>`，每个 agent 独立定时 |
| skill-creator 调用 | **传入 --agent 参数** | 生成物写入对应 agent 的 skills/ 目录 |
| A/B/C/D 路由 | **主代理负责** | 扫描所有 agent 的 pending，匹配后路由到对应 agent |

---

## 二、文件改动清单

### 2.1 handler.js（全局 Hook）

**文件：** `~/.openclaw/hooks/self-improvement/handler.js`

**改动点：**

```
1. 新增：agent 路由判断逻辑
   - 从 process.cwd() 推断当前 agent 身份
   - 规则：
     cwd 包含 /agents/<name>/ → 该 agent 的 .learnings/
     cwd 不包含 /agents/ → workspace/.learnings/（主 agent）

2. 新增：LEARNINGS_DIR 动态计算
   - 主 agent：~/.openclaw/workspace/.learnings/
   - sub-agent：<cwd>/.learnings/

3. pending 文件名加 agent 前缀
   - 旧：{ts}_{safe_name}.json
   - 新：{agent}_{ts}_{safe_name}.json
   - 例：wuji_1745404800_hook.correction.json

4. pending JSON 内容增加 agent 字段
   - 新增："agent": "<agent_name>"
```

**改动量：** 小（新增路由逻辑，不改原有写入逻辑结构）

---

### 2.2 install.sh

**文件：** `~/.openclaw/workspace/skills/self-improvement-loop/install.sh`

**改动点：**

```
1. 新增参数解析
   - --agent <name>：指定安装到的 agent
   - 无参数：安装到主 agent（默认行为）
   - 例：bash install.sh --agent wuji

2. 目录创建改为 per-agent
   - 旧：~/.openclaw/workspace/.learnings/
   - 新：~/.openclaw/workspace/.learnings/（主 agent）
         ~/.openclaw/workspace/agents/<name>/.learnings/（sub-agent）

3. 脚本安装策略改为"从全局模板复制"
   - 主 agent：~/.openclaw/workspace/scripts/self-improvement/
   - sub-agent：~/.openclaw/workspace/agents/<name>/scripts/
   - install.sh 执行时将模板脚本复制到目标 agent 目录

4. Cron job 名称加 agent 前缀
   - 旧：self-improvement-distill, self-improvement-heartbeat
   - 新：si.<agent>.distill, si.<agent>.heartbeat

5. AGENTS.md A/B/C/D 片段追加目标可配置
   - 主 agent → workspace/AGENTS.md
   - sub-agent → agents/<name>/AGENTS.md
```

**新增文件：** 无（修改 install.sh 本身）

**改动量：** 中（参数解析 + 目录判断逻辑）

---

### 2.3 distill.sh

**文件：** 每个 agent 的 `scripts/distill.sh`（从全局模板复制）

**改动点：**

```
1. 新增 --agent 参数
   - 用法：distill.sh --check-only --agent <name>
   - 不传 --agent：退化为扫描当前 cwd/.learnings/（自动判断）

2. 扫描范围改为 per-agent
   - 旧：固定扫描 ~/.openclaw/workspace/.learnings/
   - 新：扫描 $LEARNINGS_DIR（由 --agent 或 cwd 自动决定）

3. 输出文件改为 per-agent
   - 旧：~/.openclaw/workspace/.learnings/distill_output.json
   - 新：<agent_learnings>/distill_output.json

4. Threshold 可 per-agent 配置
   - 环境变量 DISTILL_THRESHOLD=2
   - 每个 agent 可设不同值
```

**改动量：** 小（增加参数解析 + 动态路径）

---

### 2.4 archive.sh / write_notified.py

**文件：** 每个 agent 的 `scripts/archive.sh`（从全局模板复制）

**改动点：**

```
1. pending 目录 per-agent
   - 旧：~/.openclaw/workspace/.learnings/.pending_notifications/
   - 新：<LEARNINGS_DIR>/.pending_notifications/

2. pending JSON 文件格式更新（见 handler.js）

3. archive.sh 同样支持 --agent 参数
```

**改动量：** 小（路径参数化）

---

### 2.5 setup_crons.py

**文件：** `~/.openclaw/workspace/skills/self-improvement-loop/scripts/setup_crons.py`

**改动点：**

```
1. cron job 名称 per-agent
   - 格式：si.<agent>.distill, si.<agent>.heartbeat
   - 避免多个 agent 的 cron 互相覆盖

2. cron sessionTarget per-agent
   - 主 agent：sessionTarget="main" 或 "isolated"
   - sub-agent：
     - 方案 A：sessionTarget="isolated"（agent 不在主 session 运行 cron）
     - 方案 B：用 agent-specific session key

3. cron schedule per-agent
   - 默认：distill 每 60min，heartbeat 每 30min
   - 不同 agent 可配置不同间隔
```

**改动量：** 中（cron 命名 + sessionTarget 逻辑）

---

### 2.6 A/B/C/D 路由逻辑（AGENTS.md）

**文件：** `~/.openclaw/workspace/AGENTS.md`（A/B/C/D 处理片段）

**改动点：**

```
1. pending 扫描范围扩大
   - 旧：扫描 ~/.openclaw/workspace/.learnings/.pending_notifications/*.json
   - 新：扫描以下所有目录中的 *.json
       - ~/.openclaw/workspace/.learnings/.pending_notifications/    （主 agent）
       - ~/.openclaw/workspace/agents/*/.learnings/.pending_notifications/ （所有 sub-agent）

2. 从文件名/内容中提取 agent 身份
   - 文件名格式：{agent}_{ts}_{safe_name}.json
   - JSON 内容字段："agent": "<name>"

3. skill-creator 调用传入 agent 参数
   - 旧：sessions_spawn → skill-creator
   - 新：sessions_spawn → skill-creator --agent <target_agent>

4. D 选项分支
   - D → 全局规则（SOUL.md / AGENTS.md / TOOLS.md）
   - D.<agent> → agent 私有规则（skills/<agent>/AGENTS.md）
   - 例：用户回复 "D.wuji" → 无极的私有规则写入无极的 skills 目录
```

**改动量：** 中（路由 + 分支逻辑）

---

### 2.7 skill-creator 调用（per-agent skills 目录）

**文件：** skill-creator 收到 --agent 参数后的行为

**改动点：**

```
1. 生成的 skill 安装到对应 agent
   - 旧：~/.openclaw/workspace/skills/<slug>/
   - 新：
       - 主 agent：~/.openclaw/workspace/skills/<slug>/
       - sub-agent：~/.openclaw/workspace/agents/<name>/skills/<slug>/

2. 新增 agent 上下文注入
   - skill-creator 在生成时需了解该 agent 的职责
   - 从 agents/<name>/SOUL.md 读取 persona 上下文
```

**改动量：** 中（skill 安装路径 + persona 注入）

---

### 2.8 新增文件

| 文件路径 | 内容 | 来源 |
|---------|------|------|
| `workspace/agents/<name>/SOUL.md` | agent 私有 persona | 手动创建或从模板初始化 |
| `workspace/agents/<name>/AGENTS.md` | agent 私有规则 | 手动创建或从模板初始化 |
| `workspace/agents/<name>/.learnings/` | learnings 数据目录 | install.sh --agent 时自动创建 |
| `workspace/agents/<name>/scripts/` | 私有脚本副本 | install.sh --agent 时从模板复制 |
| `workspace/agents/<name>/skills/` | 私有 skills 目录 | skill-creator 动态写入 |

---

## 三、实施步骤

### Phase 0：前提验证（必须先做）
```
0.1 确认 sub-agent spawn 时 process.cwd() 等于什么
    → 是 workspace root 还是 agent workspace？
    → 验证方法：启动一个 sub-agent，打印 process.cwd()
    → 结果决定 handler.js 路由策略是否可行
```

### Phase 1：handler.js 路由改造（最小闭环验证）
```
1.1 修改 handler.js，增加 cwd 推断 + 路由逻辑
1.2 重启 gateway：openclaw gateway restart
1.3 启动一个 sub-agent session，对话触发 learnings 写入
1.4 验证： learnings 写入了对应 agents/<name>/.learnings/
1.5 通过 → 进入 Phase 2；不通过 → 先解决 Phase 0 的问题
```

### Phase 2：install.sh 支持 --agent
```
2.1 修改 install.sh 支持 --agent 参数
2.2 运行：bash install.sh --agent wuji
2.3 验证：无极的 .learnings/ + scripts/ + AGENTS.md 全部创建
2.4 运行：bash install.sh --agent moling（墨灵）
2.5 验证：墨灵的数据目录结构正确（墨灵已有部分，继续完善）
```

### Phase 3：distill 脚本 per-agent
```
3.1 每个 agent 的 scripts/ 下已有 distill.sh
3.2 验证 distill.sh --check-only --agent <name> 能正常输出
3.3 验证 distill 输出写入对应 agent 的 .learnings/distill_output.json
```

### Phase 4：cron jobs per-agent
```
4.1 修改 setup_crons.py 的 job 命名逻辑
4.2 运行 install.sh --agent <name> 重新注册 cron
4.3 验证：openclaw cron list 中出现 si.<agent>.* 格式的 jobs
4.4 验证：每个 agent 的 cron 独立运行，互不覆盖
```

### Phase 5：A/B/C/D 路由改造
```
5.1 修改 AGENTS.md 中的 A/B/C/D 扫描逻辑
5.2 扫描范围从单一目录改为扫描所有 agents/
5.3 验证：pending 文件加 agent 前缀后，主代理能正确匹配
5.4 验证：skill-creator --agent 参数生效，skill 安装到正确目录
```

### Phase 6：全流程验证
```
6.1 主 agent 触发 learnings → distill → pending 通知
6.2 用户回复 A/B/C/D → 正确路由到对应 agent
6.3 D 选项 → 验证全局 vs 私有 Promotion 路径
6.4 无极 + 墨灵 + CC 全流程跑通
```

---

## 四、关键风险与依赖

### 风险 1（高优先级）
**sub-agent 的 process.cwd() 不确定**
- 如果沙盒里所有 agent 的 cwd 都是 workspace root，handler.js 路由失效
- 依赖 Phase 0 验证结果
- 缓解方案：要求 OpenClaw spawn 时设置正确的 cwd

### 风险 2（中优先级）
**pending 文件名格式变更后，旧文件无法识别**
- Phase 1 开始前，pending 目录可能已有历史 JSON
- 方案：路由逻辑同时兼容旧格式（无前缀）和新格式（有前缀）
- 新格式：{agent}_{ts}_{name}.json；旧格式：{ts}_{name}.json（默认主 agent）

### 风险 3（中优先级）
**skill-creator 生成 skill 时需要了解 agent 职责**
- 目前 skill-creator 无 --agent-context 参数
- 方案：在 skill-creator 的 prompt 模板中增加变量占位符
- 例：`## Agent Context\n{{AGENT_SOUL}}`

### 风险 4（低优先级）
**多个 agent 同时 distill，IO 竞争**
- distill 输出是写入不同 agent 目录，无竞争
- 但 cron 调度器本身可能有重复触发问题
- 方案：setup_crons.py 中每个 agent 的 cron job 用唯一名称

---

## 五、D 选项 Promotion 决策

| 用户输入 | 目标文件 | 说明 |
|---------|---------|------|
| D | SOUL.md / AGENTS.md / TOOLS.md（全局） | 跨所有 agent 都适用的规则 |
| D.wuji | agents/wuji/AGENTS.md | 无极私有规则 |
| D.moling | agents/moling/AGENTS.md | 墨灵私有规则 |

**规则：**
- 全局 Promotion 需谨慎，确保该规则确实跨 agent 通用
- 每个 agent 的私有 AGENTS.md 只在对应 agent 启动时加载
- 主代理（墨染）的私有 AGENTS.md 即 workspace/AGENTS.md

---

## 六、需向 OpenClaw 提的需求

| 需求 | 优先级 | 说明 |
|------|--------|------|
| Hook event 增加 agentId 字段 | 高 | 最干净的路由方式，减少对 cwd 的依赖 |
| sub-agent spawn 时 cwd 设置为 agent workspace | 高 | 目前不确定，需要验证 |
| Hook 支持 per-agent 注册（hook 按 session 自动路由） | 低 | 长期理想态，当前 handler.js 内路由已可解决 |
