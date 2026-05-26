# Pattern Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable AI-driven root cause analysis, skill correlation, and A/B/C/D decision support by adding `raw_md` field to `manager.py scan` and generating analysis JSON in cron prompt.

**Architecture:** Follows "scripts do mechanics, AI does semantics" principle:
- `manager.py scan` outputs `raw_md` (mechanical) — entry rendered as Markdown
- Cron AI prompt generates `analysis.json` (semantic) — root cause + skill matching + D recommendation

**Tech Stack:** Python 3, JSON, standard library only

---

## File Structure

| File | Role |
|------|------|
| `scripts/manager.py` | Modify: add `raw_md` field in scan output |
| `scripts/cron-payloads.json` | Modify: add analysis.json generation logic in AI prompt |
| `scripts/agents-append.md` | Verify: execution reads analysis.json |

---

## Tasks

### Task 1: Add `raw_md` Field to manager.py scan

**Files:**
- Modify: `scripts/manager.py:251-256`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manager_scan_raw_md.py
def test_scan_includes_raw_md():
    """scan output should include raw_md field for each entry"""
    import subprocess, json, tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal learnings dir
        learnings = os.path.join(tmpdir, '.learnings')
        os.makedirs(learnings)
        # Write a test entry
        with open(os.path.join(learnings, 'learnings.jsonl'), 'w') as f:
            f.write(json.dumps({
                'id': 'test-001',
                'pattern_key': 'test-pattern',
                'what_happened': 'Something happened',
                'root_cause': 'Root cause here',
                'how_to_avoid': 'Avoid this way',
                'status': 'pending',
                'notified': False,
                'notification_count': 0
            }) + '\n')

        result = subprocess.run(
            ['python3', 'scripts/manager.py', '--learnings-dir', learnings, 'scan', '--trigger-only'],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        entry = data['patterns'][0]['entries'][0]

        assert 'raw_md' in entry, f"raw_md missing: {entry.keys()}"
        assert '### What Happened' in entry['raw_md']
        assert '### Root Cause' in entry['raw_md']
        assert '### How To Avoid' in entry['raw_md']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_manager_scan_raw_md.py -v`
Expected: FAIL with "raw_md missing"

- [ ] **Step 3: Write the `_entry_to_raw_md` helper function**

Add after line 220 (before `cmd_scan`):

```python
def _entry_to_raw_md(e):
    """Render a JSON entry as Markdown for AI analysis."""
    sections = []
    sections.append(f"### What Happened\n{e.get('what_happened', '')}")
    sections.append(f"### Root Cause\n{e.get('root_cause', '')}")
    sections.append(f"### How To Avoid\n{e.get('how_to_avoid', '')}")
    if e.get('tags'):
        sections.append(f"### Tags\n{', '.join(e.get('tags', []))}")
    if e.get('skill_candidate'):
        sections.append(f"### Suggested Skill\n{e.get('skill_candidate')}")
    return '\n\n'.join(sections)
```

- [ ] **Step 4: Modify cmd_scan to add raw_md to each entry**

In `cmd_scan` (line 251-256), change:

```python
patterns.append({
    'name': name, 'count': count, 'threshold': args.threshold,
    'should_notify': should_notify, 'source': group['source'],
    'first_entry': first,
    'entries': group['entries'][:max_entries],
})
```

To:

```python
# Add raw_md to each entry for AI analysis
for entry in group['entries'][:max_entries]:
    entry['raw_md'] = _entry_to_raw_md(entry)

patterns.append({
    'name': name, 'count': count, 'threshold': args.threshold,
    'should_notify': should_notify, 'source': group['source'],
    'first_entry': first,
    'entries': group['entries'][:max_entries],
})
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_manager_scan_raw_md.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/manager.py tests/test_manager_scan_raw_md.py
git commit -m "feat(self-improvement): add raw_md field in scan output"
```

---

### Task 2: Add analysis.json Generation to Cron Prompt

**Files:**
- Modify: `scripts/cron-payloads.json` message field

- [ ] **Step 1: Read current cron-payloads.json message**

The AI prompt currently has:
- Step 3b) "阅读 raw_md" — now possible since raw_md is provided
- Step 4 "pending JSON" — missing generation logic

- [ ] **Step 2: Add Step 3.5 - Generate analysis.json**

Insert between Step 3 and Step 4 in the message:

```
## Step 3.5: 生成 analysis.json（每个 pattern 一个）

对每个需要通知的 pattern，在发送通知前先生成分析文件：

PENDING_DIR="${LEARNINGS_DIR}/.pending_notifications"
mkdir -p "$PENDING_DIR"

对每个 pattern_key 生成：
${PENDING_DIR}/{pattern_key}.analysis.json

格式：
{
  "pattern_key": "[pattern_key]",
  "analysis": {
    "root_cause_summary": "[从 entries 聚合的根因摘要，2-3 句话]",
    "urgency": "[high/medium/low — 基于 count 和时间跨度]",
    "entries_sample": "[前 2-3 条 entry 的 what_happened 摘要]",
    "skill_candidates": ["[可能相关的 skill 名称列表]"],
    "related_skills": [
      {"path": "skills/xxx/SKILL.md", "score": 0.85, "reason": "[匹配理由]"}
    ],
    "d_recommendation": {
      "target": "[SOUL.md|AGENTS.md|TOOLS.md]",
      "reason": "[为什么升华到这个文件]"
    },
    "suggested_action": "[A|B|C|D — 基于分析的建议]",
    "confidence": 0.75
  },
  "generated_at": "[ISO timestamp]"
}
```

生成后继续 Step 4。

- [ ] **Step 3: Fix Step 4 - Use correct manager.py commands**

当前 Step 4 引用了不存在的 `archive --write-notified` 参数。改为：

```
## Step 4: 写回 notified 状态（v5.0.0）

对每个已发送通知的 pattern：
1. 调用 manager.py notify 标记该 pattern 所有 entries 为已通知
2. 写 analysis.json 到 .pending_notifications/

bash ~/.openclaw/workspace/skills/self-improvement-loop/scripts/manager.py \
  --learnings-dir "$LEARNINGS_DIR" notify [entry_id]
```

- [ ] **Step 4: Commit**

```bash
git add scripts/cron-payloads.json
git commit -m "feat(self-improvement): add analysis.json generation in cron prompt"
```

---

### Task 3: Create .pending_notifications/ Directory Support

**Files:**
- Modify: `scripts/manager.py` add `pending` command

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manager_pending.py
def test_manager_pending_command_exists():
    """manager.py should have pending command to manage pending_notifications"""
    result = subprocess.run(
        ['python3', 'scripts/manager.py', '--help'],
        capture_output=True, text=True
    )
    assert 'pending' in result.stdout, "pending subcommand missing"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_manager_pending.py -v`
Expected: FAIL with "pending subcommand missing"

- [ ] **Step 3: Add pending subparser and cmd_pending function**

Add after `cmd_stat` (line 301):

```python
def cmd_pending(args):
    """Manage .pending_notifications/ directory"""
    pending_dir = os.path.join(LEARNINGS_DIR, '.pending_notifications')
    os.makedirs(pending_dir, exist_ok=True)

    if args.list:
        files = sorted(os.listdir(pending_dir))
        for f in files:
            print(f)
        return

    if args.clean:
        for f in os.listdir(pending_dir):
            os.remove(os.path.join(pending_dir, f))
        print(f"Cleaned {pending_dir}")
        return

    if args.write:
        pattern_key = args.write
        content = sys.stdin.read()
        outfile = os.path.join(pending_dir, f'{pattern_key}.analysis.json')
        with open(outfile, 'w') as f:
            f.write(content)
        print(f"Wrote {outfile}")
```

Add to main() after `stat` parser (line 348):

```python
p = subparsers.add_parser('pending')
p.add_argument('--list', action='store_true', help='List pending files')
p.add_argument('--clean', action='store_true', help='Clean pending directory')
p.add_argument('--write', metavar='PATTERN_KEY', help='Write analysis JSON from stdin')
```

Add to commands dict (line 353):

```python
'pending': cmd_pending,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_manager_pending.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/manager.py tests/test_manager_pending.py
git commit -m "feat(self-improvement): add pending command for analysis.json management"
```

---

### Task 4: Update agents-append.md to Read analysis.json

**Files:**
- Modify: `scripts/agents-append.md`

- [ ] **Step 1: Read current agents-append.md**

Current A/B/C/D execution reads pending JSON but doesn't use analysis.

- [ ] **Step 2: Update A/B/C/D sections to read analysis.json**

在每个 A/B/C/D 执行前，读取对应的 `.analysis.json` 文件：

```markdown
### 执行前准备

在执行 A/B/C/D 前：
1. 读取 `${LEARNINGS_DIR}/.pending_notifications/{pattern_key}.analysis.json`
2. 参考 `analysis.suggested_action` 和 `analysis.related_skills`
3. 如果 analysis 中有 skill_candidates，优先使用
```

- [ ] **Step 3: Commit**

```bash
git add scripts/agents-append.md
git commit -m "feat(self-improvement): update agents-append to read analysis.json"
```

---

### Task 5: Run Full Test Suite

- [ ] **Step 1: Run all tests**

Run: `python3 -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify scan output includes raw_md**

Run: `python3 scripts/manager.py scan --trigger-only | python3 -c "import sys,json; d=json.load(sys.stdin); print('raw_md' in str(d))"`
Expected: True

- [ ] **Step 3: Commit all changes**

```bash
git add -A
git commit -m "feat(self-improvement): complete Pattern Analysis implementation

- manager.py scan outputs raw_md for AI analysis
- cron prompt generates analysis.json per pattern
- pending command manages analysis files
- agents-append reads analysis for A/B/C/D decision support"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| raw_md field in scan | Task 1 |
| Root cause analysis in cron prompt | Task 2 |
| Skill correlation analysis | Task 2 |
| D recommendation (SOUL/AGENTS/TOOLS) | Task 2 |
| analysis.json generation | Task 2 |
| .pending_notifications/ directory | Task 3 |
| A/B/C/D execution reads analysis | Task 4 |

All spec requirements covered.