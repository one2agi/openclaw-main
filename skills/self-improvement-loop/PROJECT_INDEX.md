# Project Index: self-improvement-loop

**Generated**: 2026-05-26
**Version**: 5.0.0
**Purpose**: Per-agent feedback loop for OpenClaw — captures corrections/errors/features, detects patterns per agent workspace, notifies via per-agent channel bot, and executes A/B/C/D decisions.

---

## 📁 Project Structure

```
self-improvement-loop/
├── SKILL.md              # Main skill definition (v5.0.0)
├── install.sh            # Installation script (v5.0.0)
├── scripts/
│   ├── manager.py        # ★ Core: unified CLI tool (v5.0.0)
│   ├── cron_runner.sh    # Per-agent cron executor (v5.0.0)
│   ├── setup_crons.py    # Create per-agent cron jobs
│   ├── session_state.sh  # Session state tracking
│   ├── inject_review.sh  # Self-review prompt generator (JSON output)
│   └── agents-append.md # A/B/C/D handling logic
├── hooks/
│   ├── handler.js        # Event handler (v5.0.0)
│   └── HOOK.md          # Hook documentation
├── tests/
│   └── test_manager.py   # TDD tests for manager.py (24 tests)
├── docs/
│   └── REDESIGN.md      # v5.0.0 redesign documentation
└── references/
    └── setup-guide.md   # Setup documentation
```

---

## 🚀 Entry Points

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill entry — defines the self-improvement loop mechanism |
| `install.sh` | Installs skill — creates workspaces, bindings, crons |
| `hooks/handler.js` | Event handler — processes bootstrap, commands, messages |
| `scripts/manager.py` | Unified data management — CRUD, scan, archive |
| `scripts/setup_crons.py` | Creates per-agent cron jobs via Gateway API |

---

## 📦 Core Modules

### `scripts/manager.py`
- **Purpose**: Unified CLI tool for all data operations
- **Commands**:
  - `add` — Add new entry (atomic append)
  - `list` — List/filter entries
  - `get` — Get single entry
  - `update` — Update entry fields
  - `notify` — Mark entry as notified
  - `scan` — Pattern detection (replaces distill.sh)
  - `archive` — Archive resolved entries (replaces archive.sh)
  - `stat` — Statistics summary

### `hooks/handler.js`
- **Purpose**: OpenClaw hook for event-driven self-improvement capture
- **Key Functions**:
  - `extractAgentId(sessionKey)` — parse agent ID from session
  - `getAgentWorkspace(agentId)` — route to correct workspace
  - `getLearningsDir(sessionKey)` — get per-agent `.learnings/` path
  - `containsKeyword(text, keywords)` — keyword detection
  - Calls `manager.py add --json` instead of writing MD

### `scripts/distill.sh`
- **REPLACED** by `manager.py scan`

### `scripts/archive.sh`
- **REPLACED** by `manager.py archive`

### `scripts/write_notified.py`
- **REPLACED** by `manager.py update` and `manager.py notify`

---

## 🔧 Configuration

| File | Purpose |
|------|---------|
| `openclaw.json` | Source of agent list + channel bindings |
| `scripts/cron-payloads.json` | Cron job templates per agent |

---

## 📚 Documentation

| File | Topic |
|------|-------|
| `SKILL.md` | Full skill documentation, data flow, permissions |
| `hooks/HOOK.md` | Hook behavior and event types |
| `references/setup-guide.md` | Installation guide |
| `docs/REDESIGN.md` | v5.0.0 redesign documentation |

---

## 🧪 Test Coverage

- **Framework**: pytest
- **Files**: `test_manager.py` (24 tests)
- **Location**: `tests/` directory
- **All tests**: PASSED ✅

---

## 🔗 Key Dependencies

| Dependency | Purpose |
|------------|---------|
| OpenClaw | Host platform — provides hook system, cron, gateway API |
| Python3 (≥3.8) | manager.py |
| Node.js | handler.js |
| skill-creator | Path A - create skills |
| skill-improvement | Path B - improve skills |

---

## 📝 Quick Start

1. **Install**: `bash install.sh` — sets up per-agent workspaces + crons
2. **Bootstrap**: OpenClaw loads `hooks/handler.js` on agent startup
3. **Capture**: User corrections → hook detects → `manager.py add --json`
4. **Scan**: Hourly cron (`self-improvement-{agent}`) runs `manager.py scan`
5. **Notify**: Pattern detected → notification via channel bot
6. **Execute**: User replies A/B/C/D → agents-append.md handles

---

## Data Storage (v5.0.0)

```
~/.openclaw/workspace/agents/{agent-id}/.learnings/
├── learnings.jsonl   # Append-only entries
├── errors.jsonl      # Append-only entries
├── features.jsonl    # Append-only entries
└── archive/
    └── {YYYY-MM}.jsonl  # Archived entries
```
