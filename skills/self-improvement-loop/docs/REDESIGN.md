# Self-Improvement Loop — v5.0.0 重构设计文档

**版本**: 5.0.0-draft  
**日期**: 2026-05-26  
**状态**: 设计中  
**目标**: 100% 机器确定性 + 零解析失败 + Agent-Native 工作流

---

## 1. 设计原则

| 原则 | 具体要求 |
|------|----------|
| **确定性优先** | 所有数据操作 100% 可复现，无歧义解析 |
| **Append-Only** | 从不覆写，只追加；状态变更通过新字段而非原地编辑 |
| **单一数据源** | 一个 manager.py 处理所有 IO，无其他脚本直接读写文件 |
| **Agent-Native** | Agent 通过 CLI 调用而非文档编辑，JSON 输入/输出 |
| **原子性写入** | 所有写操作使用 tempfile + rename 保证不丢数据 |

---

## 2. 数据模型

### 2.1 Entry Schema（所有条目的统一格式）

```json
{
  "id": "LRN-20260526-001",
  "type": "learnings",
  "logged_at": "2026-05-26T10:30:00+08:00",
  "status": "pending",
  "category": "correction",
  "pattern_key": "hook.correction.forgot-to-verify",
  "what_happened": "在验证文件存在性后没有检查文件内容是否为空",
  "root_cause": "对 API 返回值假设了非空的边界条件",
  "how_to_avoid": "始终检查返回值是否为 None 或空集合",
  "tags": ["file-io", "defensive"],
  "notified": false,
  "notification_count": 0,
  "updated_at": null,
  "source": "human_correction"
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 格式: `{PREFIX}-{YYYYMMDD}-{NNN}`，PREFIX: LRN/ERR/FEAT |
| `type` | enum | ✓ | `learnings` / `errors` / `features` |
| `logged_at` | ISO8601 | ✓ | 条目创建时间 |
| `status` | enum | ✓ | `pending` / `active` / `in_progress` / `resolved` / `promoted` / `dormant` |
| `category` | string | ✓ | learnings: `correction\|best_practice\|insight\|knowledge_gap`; errors: `error`; features: `feature_request` |
| `pattern_key` | string | ○ | 格式 `source.type.identifier`，唯一标识 recurrence |
| `what_happened` | string | ✓ | 描述场景（Agent 可直接使用） |
| `root_cause` | string | ○ | 结构化原因分析 |
| `how_to_avoid` | string | ○ | 可操作的原则 |
| `tags` | string[] | ○ | 自由标签 |
| `notified` | boolean | ✓ | 是否已发送通知 |
| `notification_count` | integer | ✓ | 累计通知次数 |
| `updated_at` | ISO8601 | ○ | 最后更新时间 |
| `source` | enum | ✓ | `human_correction` / `inject_review` / `feature_request` / `migrated` |

### 2.2 存储文件

```
.learnings/
├── learnings.jsonl      # Append-only，所有 learn 条目
├── errors.jsonl         # Append-only，所有 error 条目
├── features.jsonl       # Append-only，所有 feature 条目
├── archive/
│   └── {YYYY-MM}.jsonl # 归档数据（resolved/promoted 的条目）
├── .pending/
│   └── {ts}_{pattern_key}.json  # 待通知队列
└── .lock/              # 目录锁文件（防止并发写）
    └── lock
```

**为什么用 JSONL 而不是 SQLite**:
- JSONL 是纯文本，可用 `grep`/`jq` 快速调试
- 不引入额外依赖（SQLite 需要 native 绑定）
- 追加写入无锁竞争（SQLite 写需要 journal）
- 单文件备份/同步更简单

### 2.3 ID 生成规则

```
PREFIX = {LRN|ERR|FEAT}
YYYYMMDD = 当天日期
NNN = 当天该类型第 N 个条目（从 001 起）
示例: LRN-20260526-001, ERR-20260526-001, FEAT-20260526-003
```

**同一日期同一类型累加，不同类型独立计数。**

---

## 3. manager.py CLI 设计

### 3.1 命令总览

```bash
python manager.py <command> [options]

Commands:
  add         添加新条目（追加写入）
  list        列出条目（支持过滤）
  get         获取单个条目
  update      更新条目字段（原子性覆写）
  notify      标记条目已通知（原子性更新 notified + notification_count）
  scan        扫描模式，输出聚合报告（替代 distill.sh）
  archive     归档 resolved/promoted 条目（替代 archive.sh）
  render      将 JSONL 渲染为 Markdown（可选的人类可读视图）
  migrate     从现有 MD 文件迁移到 JSONL
  stat        统计摘要
```

### 3.2 add — 添加条目

```bash
# 交互式添加（Agent 最常用）
python manager.py add --type learnings

# JSON 文件添加（Agent-Native 方式）
python manager.py add --json data.json

# 命令行参数添加
python manager.py add \
  --type learnings \
  --category correction \
  --pattern-key hook.correction.forgot-to-verify \
  --what "描述..." \
  --root-cause "原因..." \
  --avoid "下次如何做..." \
  --tags tag1,tag2
```

**输入 schema (--json)**:

```json
{
  "type": "learnings",
  "category": "correction",
  "pattern_key": "hook.correction.forgot-to-verify",
  "what_happened": "...",
  "root_cause": "...",
  "how_to_avoid": "...",
  "tags": ["tag1"],
  "source": "human_correction"
}
```

**输出**:

```json
{
  "success": true,
  "entry": { /* 完整的 entry 对象，包含生成的 id */ },
  "file": "~/.openclaw/workspace/agents/code-dev/.learnings/learnings.jsonl"
}
```

**原子性保证**:
1. 写入 tempfile
2. fsync 到磁盘
3. rename 到目标文件
4. 失败则原文件不变

### 3.3 list — 列出条目

```bash
# 列出所有 pending 条目
python manager.py list --status pending

# 列出特定类型
python manager.py list --type errors --status active

# 过滤 pattern_key
python manager.py list --pattern-key hook.correction.*

# 统计 count（不输出详情）
python manager.py list --type learnings --count-only

# JSON 输出（供 Cron 使用）
python manager.py list --status pending --format json
```

**输出示例 (--format json)**:

```json
{
  "entries": [
    {
      "id": "LRN-20260526-001",
      "type": "learnings",
      "category": "correction",
      "status": "pending",
      "pattern_key": "hook.correction.forgot-to-verify",
      "what_happened": "...",
      "notified": false,
      "notification_count": 0
    }
  ],
  "total": 1
}
```

### 3.4 scan — 模式检测（替代 distill.sh）

```bash
# 标准扫描（阈值=2）
python manager.py scan

# 自定义阈值
python manager.py scan --threshold 3

# 错误模式扫描（ERRORS.md 专用阈值=1）
python manager.py scan --type errors --threshold 1

# 仅返回可触发通知的条目
python manager.py scan --trigger-only
```

**scan 输出 schema**:

```json
{
  "patterns": [
    {
      "pattern_key": "hook.correction.forgot-to-verify",
      "count": 3,
      "threshold": 2,
      "should_notify": true,
      "source": "pattern_key",
      "first_entry": { /* 第一个条目的完整对象 */ },
      "entries": [ /* 所有匹配条目 */ ]
    }
  ],
  "category_fallback": [
    {
      "category": "correction",
      "count": 2,
      "threshold": 2,
      "should_notify": true,
      "source": "category",
      "first_entry": { /* 第一个条目 */ }
    }
  ],
  "meta": {
    "scanned_at": "2026-05-26T10:00:00+08:00",
    "threshold": 2,
    "files_scanned": ["learnings.jsonl", "errors.jsonl", "features.jsonl"],
    "total_entries": 15,
    "pending_entries": 8
  }
}
```

**scan 逻辑**:
1. 读取所有 jsonl 文件，加载全部 entry
2. 按 `pattern_key` 分组（忽略 null/空）
3. 按 `category` 分组（仅针对无 pattern_key 的条目）
4. 计算每组 count
5. 判断 `should_notify = (count >= threshold) AND (notified == false OR notification_count < count)`
6. 返回 patterns + category_fallback

### 3.5 update — 更新条目

```bash
# 更新状态
python manager.py update LRN-20260526-001 --status resolved

# 批量更新状态（所有 pending → dormant）
python manager.py update --type learnings --status pending --set-status dormant

# 更新 pattern_key
python manager.py update LRN-20260526-001 --pattern-key hook.correction.new-key
```

**原子性保证**:
1. 读取完整 jsonl
2. 找到目标 entry，生成新版本（updated_at = now）
3. 写 tempfile
4. rename
5. 原文件保留（不做 in-place 编辑）

### 3.6 notify — 标记已通知

```bash
# 标记单个条目
python manager.py notify LRN-20260526-001

# 批量通知（根据 scan 结果）
python manager.py notify --from-scan --threshold 2
```

**语义**: `notified=true`, `notification_count += 1`, `updated_at = now`

### 3.7 archive — 归档

```bash
# 干跑（预览）
python manager.py archive --dry-run

# 执行归档
python manager.py archive

# 归档指定月份
python manager.py archive --month 2026-05
```

**归档逻辑**:
1. 找出所有 `status IN (resolved, promoted)` 的条目
2. 写入 `archive/{YYYY-MM}.jsonl`（追加模式）
3. 从源 jsonl 文件中**移除**这些条目（重写文件，不 in-place 编辑）
4. 清理 `.pending/` 中超期（>7天）的文件

**注意**: 归档是**移动**操作，原 jsonl 文件会被重写。

### 3.8 render — Markdown 渲染（可选）

```bash
# 渲染单类型
python manager.py render --type learnings

# 渲染所有类型到标准路径
python manager.py render --all

# 指定输出路径
python manager.py render --type learnings --output /path/to/LEARNINGS.md
```

**用途**: 仅用于人类可读性查看，**不作为数据存储**。渲染输出纯展示，不参与任何逻辑。

### 3.9 migrate — MD 迁移

```bash
# 迁移所有 MD 文件
python manager.py migrate --learnings-dir .learnings/

# 干跑预览
python manager.py migrate --learnings-dir .learnings/ --dry-run
```

**迁移逻辑**:
1. 解析 LEARNINGS.md / ERRORS.md / FEATURE_REQUESTS.md
2. 每条 entry 转换为 JSON schema
3. 写入对应的 jsonl 文件
4. **保留原 MD 文件**（加 `.migrated` 后缀）

---

## 4. handler.js 改造

### 4.1 改造后的行为

```javascript
// handler.js — v5.0.0
// 不再直接写 MD，改为调用 manager.py

const handler = async (event) => {
  // ... keyword detection ...

  if (isCorrection || isErrorFeedback || isFeatureRequest) {
    // 构造 JSON 数据
    const entryData = {
      type: isCorrection ? 'learnings' : isErrorFeedback ? 'errors' : 'features',
      category: isCorrection ? 'correction' : isErrorFeedback ? 'error' : 'feature_request',
      what_happened: extractedText,
      source: 'human_correction'
    };

    // 写入临时 JSON 文件
    const tmpFile = `/tmp/self-improvement-${Date.now()}.json`;
    require('fs').writeFileSync(tmpFile, JSON.stringify(entryData));

    // 调用 manager.py add
    execSync(`python3 ${MANAGER_PY} add --json ${tmpFile}`, { encoding: 'utf8' });

    // 清理
    require('fs').unlinkSync(tmpFile);

    // 推送提醒
    event.context.messages?.push(
      `[Self-Improvement] 已记录到 ${learningsDir}`
    );
  }
};
```

### 4.2 inject_review.sh 改造

不再生成 Markdown 模板，改为生成 JSON 或命令行参数：

```bash
#!/bin/bash
# inject_review.sh — v5.0.0
# 生成 JSON 格式的 entry 模板，供 Agent 填充后调用 manager.py add

LEARNINGS_DIR="${LEARNINGS_DIR:-$(pwd)/.learnings}"
MANAGER_PY="$(dirname "$0")/manager.py"

python3 << 'PYEOF'
import os, json, datetime

template = {
    "type": "learnings",
    "category": "correction",
    "pattern_key": "",
    "what_happened": "",
    "root_cause": "",
    "how_to_avoid": "",
    "tags": [],
    "source": "inject_review"
}

print(json.dumps(template, ensure_ascii=False, indent=2))
PYEOF
```

Agent 使用方式：
1. hook 推送 `inject_review.sh` 输出（JSON 模板）
2. Agent 填充后执行 `manager.py add --json /tmp/review.json`
3. 系统自动处理

---

## 5. Cron 改造

### 5.1 新的 Cron 逻辑

```bash
#!/bin/bash
# self-improvement-{agent} cron — v5.0.0

AGENT_ID="code-dev"
LEARNINGS_DIR="$HOME/.openclaw/workspace/agents/$AGENT_ID/.learnings"
MANAGER_PY="$HOME/.openclaw/workspace/skills/self-improvement-loop/scripts/manager.py"

# 1. Scan for patterns
SCAN_RESULT=$(python3 "$MANAGER_PY" scan --threshold 2)

# 2. Check if any should_notify
SHOULD_NOTIFY=$(echo "$SCAN_RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
patterns = d.get('patterns', []) + d.get('category_fallback', [])
return any(p.get('should_notify', False) for p in patterns)
")

if [ "$SHOULD_NOTIFY" = "True" ]; then
    # 3. Send notification via channel bot
    NOTIFICATION=$(echo "$SCAN_RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
# format notification message
...")
    # ... send notification ...

    # 4. Mark as notified
    echo "$SCAN_RESULT" | python3 "$MANAGER_PY" notify --from-scan
fi

# 5. Archive resolved entries (daily)
python3 "$MANAGER_PY" archive
```

### 5.2 cron-payloads.json 改造

```json
{
  "crons": [
    {
      "name": "self-improvement-{agent}",
      "schedule": "0 * * * *",
      "command": "bash {SKILL_DIR}/scripts/cron_runner.sh {agent}",
      "agent": "{agent}",
      "delivery": {
        "channel": "{channel}",
        "accountId": "{accountId}"
      }
    }
  ]
}
```

---

## 6. 文件结构（重构后）

```
self-improvement-loop/
├── SKILL.md                    # 更新文档引用 manager.py
├── install.sh                  # 改造：创建 .learnings/ 和 cron
├── scripts/
│   ├── manager.py              # ★ 核心：统一 CLI 工具
│   ├── setup_crons.py          # 保持不变（创建 cron）
│   ├── session_state.sh        # 保持不变（已经是 JSON）
│   ├── cron_runner.sh          # ★ 新增：Cron 执行器
│   └── migrate_to_jsonl.py     # ★ 新增：MD → JSONL 迁移脚本
├── hooks/
│   ├── handler.js              # 改造：调用 manager.py
│   └── HOOK.md
├── docs/
│   ├── REDESIGN.md             # 本文档
│   └── MANAGER.md              # ★ 新增：manager.py 使用手册
├── learnings/                   # ★ 迁移后 .migrated 备份
├── references/
│   └── setup-guide.md
└── tests/
    ├── test_manager.py          # ★ 新增：manager.py 单元测试
    ├── test_handler.py
    └── test_migrate.py          # ★ 新增：迁移测试
```

**删除的文件**:
- `scripts/distill.sh` — 逻辑移入 manager.py scan
- `scripts/distill_json.py` — 逻辑移入 manager.py scan
- `scripts/archive.sh` — 逻辑移入 manager.py archive
- `scripts/write_notified.py` — 逻辑移入 manager.py notify/update
- `scripts/inject_review.sh` — 简化为生成 JSON 模板

---

## 7. 迁移计划

### Phase 1: manager.py 实现
- 实现所有 CLI 命令
- 原子性写入保证
- 完整的单元测试

### Phase 2: handler.js 改造
- 更新 keyword detection
- 调用 manager.py add
- inject_review.sh 输出 JSON

### Phase 3: Cron 改造
- cron_runner.sh 实现
- scan → notify → archive 流程

### Phase 4: 迁移脚本
- migrate_to_jsonl.py 实现
- 干跑测试
- 执行迁移

### Phase 5: 清理
- 删除旧的 shell 脚本
- 更新文档
- 端到端测试

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|----------|
| JSON 解析失败 | 报错退出，不写入任何文件 |
| 文件不存在 | 自动创建空 jsonl 文件 |
| 并发写入 | 目录锁（flock），超时放弃 |
| ID 冲突 | 读取文件检查 ID 唯一性，重复则用更高序号 |
| 迁移失败 | 保留原 MD，不删除，报告错误 |
| manager.py 不存在 | hook 降级为静默忽略（不阻断主流程） |

---

## 9. 向后兼容性

### 9.1 现有 MD 文件

迁移后，原 `.md` 文件重命名为 `.migrated-{timestamp}.md`，保留备查。

### 9.2 现有 Cron

旧的 `distill.sh --check-only` 调用需更新为 `manager.py scan`。install.sh 更新时自动重建 cron。

### 9.3 现有 A/B/C/D 逻辑

`scripts/agents-append.md` 保持不变，逻辑引用路径更新即可。

---

## 10. 测试策略

### 10.1 单元测试 (test_manager.py)

```python
def test_add_entry_atomic():
    """添加条目后，原文件内容不变（原子性）"""

def test_scan_aggregation():
    """相同 pattern_key 的条目正确聚合"""

def test_notify_increments_count():
    """notify 命令正确累加 notification_count"""

def test_archive_removes_from_source():
    """归档后源文件不再包含该条目"""

def test_concurrent_write():
    """并发写入不丢数据"""
```

### 10.2 集成测试

```bash
# 模拟完整流程
python manager.py add --type learnings --what "test"
python manager.py list --type learnings
python manager.py update LRN-YYYYMMDD-001 --status resolved
python manager.py archive
python manager.py scan
```

---

## 11. 设计验证清单

- [ ] 所有文件 IO 经过 manager.py，无直接读写
- [ ] Append-only：从不 in-place 编辑 jsonl
- [ ] 原子性写入：tempfile + rename + fsync
- [ ] scan 输出 100% 可复现（相同输入 → 相同输出）
- [ ] ID 唯一性保证
- [ ] 并发安全（flock）
- [ ] 迁移不掉数据
- [ ] Agent 可通过 --json 调用完整流程
- [ ] 旧的 MD 文件可完整迁移
- [ ] Cron 逻辑可零配置迁移
