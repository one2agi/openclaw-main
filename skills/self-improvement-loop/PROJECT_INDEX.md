# Project Index: self-improvement-loop

**Generated**: 2026-05-25  
**Version**: 4.6.13  
**Purpose**: Per-agent feedback loop for OpenClaw — captures corrections/errors/features, detects patterns per agent workspace, notifies via per-agent channel bot, and executes A/B/C/D decisions.

---

## 📁 Project Structure

```
self-improvement-loop/
├── SKILL.md              # Main skill definition (v4.6.13)
├── install.sh            # Installation script (per-agent setup)
├── hooks/
│   ├── HOOK.md           # Hook documentation
│   └── handler.js        # Event handler (v4.7.0)
├── scripts/
│   ├── setup_crons.py    # Create per-agent cron jobs
│   ├── write_notified.py # Notification writer
│   ├── distill.sh        # Pattern distillation
│   ├── archive.sh        # Archive old entries
│   ├── session_state.sh  # Session state tracking
│   ├── inject_review.sh  # Self-review prompt injection
│   ├── agents-append.md  # A/B/C/D handling logic
│   └── cron-payloads.json
├── tests/                # pytest test suite
├── docs/
│   └── skill-intro.html  # Skill introduction
├── learnings/            # Template files
│   ├── LEARNINGS.md      # Corrections/best practices template
│   ├── ERRORS.md         # Error tracking template
│   └── FEATURE_REQUESTS.md
└── references/
    └── setup-guide.md    # Setup documentation
```

---

## 🚀 Entry Points

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill entry — defines the self-improvement loop mechanism |
| `install.sh` | Installs skill per-agent — creates workspaces, bindings, crons |
| `hooks/handler.js` | Event handler — processes bootstrap, commands, messages |
| `scripts/setup_crons.py` | Creates per-agent cron jobs via Gateway API |

---

## 📦 Core Modules

### `hooks/handler.js`
- **Purpose**: OpenClaw hook for event-driven self-improvement capture
- **Key Functions**:
  - `extractAgentId(sessionKey)` — parse agent ID from session
  - `getAgentWorkspace(agentId)` — route to correct workspace
  - `getLearningsDir(sessionKey)` — get per-agent `.learnings/` path
  - `containsKeyword(text, keywords)` — keyword detection
  - `generateSelfReviewPrompt(learningsDir)` — inject Hermes-style review

### `scripts/setup_crons.py`
- **Purpose**: Creates per-agent cron jobs via Gateway API
- **Key Functions**:
  - Reads `openclaw.json` for agents + bindings
  - Creates `self-improvement-{agent}` cron per agent
  - Each cron has `--agent` flag + channel delivery bindings

### `scripts/distill.sh`
- **Purpose**: Pattern detection from learnings
- **Behavior**: Scans per-agent learnings, detects recurring patterns (count≥2)

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
| `learnings/LEARNINGS.md` | Learning entry template with categories |
| `references/setup-guide.md` | Installation guide |

---

## 🧪 Test Coverage

- **Framework**: pytest
- **Files**: 4 test files (`test_handler_error_detection.py`, `test_periodic_nudge.py`, `test_single_error_notification.py`)
- **Location**: `tests/` directory with `conftest.py`

---

## 🔗 Key Dependencies

| Dependency | Purpose |
|------------|---------|
| OpenClaw | Host platform — provides hook system, cron, gateway API |
| Python (pytest) | Testing framework |
| Bash scripts | Shell operations (distill, archive, session_state) |

---

## 📝 Quick Start

1. **Install**: `bash install.sh` — sets up per-agent workspaces + crons
2. **Bootstrap**: OpenClaw loads `hooks/handler.js` on agent startup
3. **Capture**: User corrections → hook detects → writes to `agents/{id}/.learnings/`
4. **Scan**: Hourly cron (`self-improvement-{agent}`) scans for patterns
5. **Notify**: Pattern detected → notification via channel bot
6. **Execute**: User replies A/B/C/D → skill-improvement runs in correct agent session