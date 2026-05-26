#!/bin/bash
# install.sh — self-improvement-loop v5.0.0 installer
# v5.0.0: JSONL-based storage, manager.py unified interface
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${HOME}/.openclaw/workspace"
CANONICAL_DIR="$WORKSPACE/skills/self-improvement-loop/scripts"
CANONICAL_HOOKS="${HOME}/.openclaw/hooks/self-improvement"
SKILL_HOOKS="$SCRIPT_DIR/hooks"
OPENCLAW_JSON="${HOME}/.openclaw/openclaw.json"

echo "=== self-improvement-loop v5.0.0 installer ==="
echo ""

# ── Pre-flight ───────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "[✗] python3 not found"
    exit 1
fi
echo "[✓] python3: found"

# ── Helper: load per-agent workspaces ────────────────────
load_agent_workspaces() {
    python3 -c "
import json, os
path = os.path.expanduser('$OPENCLAW_JSON')
if not os.path.exists(path):
    print(''); exit()
with open(path) as f:
    d = json.load(f)
agents = d.get('agents', {}).get('list', [])
for agent in agents:
    aid = agent.get('id', 'main')
    ws = agent.get('workspace', os.path.expanduser('~/.openclaw/workspace'))
    print(f'{aid}:{ws}')
" 2>/dev/null
}

# ── 1. Create directories ───────────────────────────────
echo "[1/5] Creating per-agent .learnings directories..."
mkdir -p "$CANONICAL_HOOKS"

AGENTS_INFO=$(load_agent_workspaces)
if [ -n "$AGENTS_INFO" ]; then
    echo "$AGENTS_INFO" | while IFS=: read -r agent_id workspace; do
        agent_learnings="${workspace}/.learnings"
        mkdir -p "$agent_learnings"
        mkdir -p "$agent_learnings/archive"

        # Initialize empty JSONL files (append-only storage)
        for f in learnings errors features; do
            touch "$agent_learnings/${f}.jsonl"
        done

        echo "    ✓ $agent_id: $agent_learnings"
    done
else
    # Fallback: main workspace
    mkdir -p "$WORKSPACE/.learnings/archive"
    for f in learnings errors features; do
        touch "$WORKSPACE/.learnings/${f}.jsonl"
    done
    echo "    ✓ main: $WORKSPACE/.learnings"
fi

# ── 2. Install Hook ────────────────────────────────────
echo ""
echo "[2/5] Installing Hook..."
cp "$SKILL_HOOKS/handler.js" "$CANONICAL_HOOKS/handler.js"
cp "$SKILL_HOOKS/HOOK.md" "$CANONICAL_HOOKS/HOOK.md"
echo "  ✓ handler.js + HOOK.md → $CANONICAL_HOOKS/"

# ── 3. Register Hook ───────────────────────────────────
echo ""
echo "[3/5] Registering Hook..."
if grep -q '"self-improvement"' "$OPENCLAW_JSON" 2>/dev/null; then
    echo "  ✓ Hook already registered"
else
    openclaw hooks install self-improvement "$CANONICAL_HOOKS/handler.js" 2>/dev/null \
        && echo "  ✓ Hook registered" \
        || echo "  ⚠ Hook registration failed. Run manually:"
    echo "    openclaw hooks set self-improvement $CANONICAL_HOOKS/handler.js"
fi

# ── 4. Setup Cron jobs ─────────────────────────────────
echo ""
echo "[4/5] Setting up per-agent Cron jobs..."
python3 "$CANONICAL_DIR/setup_crons.py" --force 2>/dev/null \
    && echo "  ✓ Crons created" \
    || echo "  ⚠ Cron setup failed"

# ── 5. Inject A/B/C/D reference ──────────────────────
echo ""
echo "[5/5] Injecting self-improvement reference..."

SELF_IMPROVEMENT_REF="## 自我改进（A/B/C/D）

处理 A/B/C/D 之前必须查阅：
skills/self-improvement-loop/scripts/agents-append.md

"

inject_ref() {
    local target_file=$1
    local description=$2
    if [ ! -f "$target_file" ]; then
        echo "  ⚠ $description not found, skipping"
        return
    fi
    if python3 -c "
import sys
content = open('$target_file').read()
ok = 'A/B/C/D' in content and '必须查阅' in content and 'agents-append' in content
sys.exit(0 if ok else 1)
" 2>/dev/null; then
        echo "  ✓ $description already has reference"
    else
        echo "" >> "$target_file"
        echo "$SELF_IMPROVEMENT_REF" >> "$target_file"
        echo "  ✓ $description: reference injected"
    fi
}

AGENTS_INFO=$(load_agent_workspaces)
if [ -n "$AGENTS_INFO" ]; then
    echo "$AGENTS_INFO" | while IFS=: read -r agent_id workspace; do
        echo "  $agent_id:"
        inject_ref "$workspace/AGENTS.md" "  AGENTS.md"
        inject_ref "$workspace/memory.md" "  memory.md"
    done
else
    echo "  main:"
    inject_ref "$WORKSPACE/AGENTS.md" "  AGENTS.md"
    inject_ref "$WORKSPACE/memory.md" "  memory.md"
fi

# ── Done ─────────────────────────────────────────────────
echo ""
echo "=== Installation complete ==="
echo ""
echo "Restart gateway to activate:"
echo "   openclaw gateway restart"
echo ""
echo "Verify installation:"
echo "   python3 $CANONICAL_DIR/manager.py --help"
