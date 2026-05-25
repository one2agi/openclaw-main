#!/bin/bash
# install.sh — self-improvement-loop v5.0.0 installer
# Per-agent feedback loop: captures corrections, detects patterns, notifies, executes A/B/C/D

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${HOME}/.openclaw/workspace"
CANONICAL_HOOKS="${HOME}/.openclaw/hooks/self-improvement"
SKILL_HOOKS="$SCRIPT_DIR/hooks"
MANAGER_SCRIPT="$SCRIPT_DIR/scripts/manager.py"
OPENCLAW_JSON="${HOME}/.openclaw/openclaw.json"
LEARN_TEMPLATE="$SCRIPT_DIR/learnings/learn.jsonl.example"

# ─────────────────────────────────────────────────────────────
# Helper: load per-agent workspaces from openclaw.json
# Returns: agent_id:workspace pairs, one per line
# ─────────────────────────────────────────────────────────────
load_agent_workspaces() {
    python3 -c "
import json, os
path = os.path.expanduser('$OPENCLAW_JSON')
if not os.path.exists(path):
    print(''); exit()
try:
    with open(path) as f:
        d = json.load(f)
    agents = d.get('agents', {}).get('list', [])
    for agent in agents:
        aid = agent.get('id', 'main')
        ws = agent.get('workspace', os.path.expanduser('~/.openclaw/workspace'))
        print(f'{aid}:{ws}')
except:
    print('')
" 2>/dev/null
}

# ─────────────────────────────────────────────────────────────
# Helper: check if openclaw.json exists and is valid
# ─────────────────────────────────────────────────────────────
check_openclaw_json() {
    if [ -f "$OPENCLAW_JSON" ] && python3 -c "import json; json.load(open('$OPENCLAW_JSON'))" 2>/dev/null; then
        return 0
    fi
    return 1
}

# ─────────────────────────────────────────────────────────────
# Helper: run manager.py command
# ─────────────────────────────────────────────────────────────
run_manager() {
    local learnings_dir=$1
    LEARNINGS_DIR="$learnings_dir" python3 "$MANAGER_SCRIPT"
}

# ─────────────────────────────────────────────────────────────
# 0. Pre-flight
# ─────────────────────────────────────────────────────────────
echo "=== self-improvement-loop v5.0.0 installer ==="
echo ""

if ! command -v python3 &>/dev/null; then
    echo "[✗] python3 not found. This skill requires Python 3."
    exit 1
fi
echo "[✓] python3: found"

# Check python3 version
PY_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ "$(echo "$PY_VERSION < 3.8" | bc)" = "1" ]; then
    echo "[✗] Python 3.8+ required, found $PY_VERSION"
    exit 1
fi
echo "[✓] Python version: $PY_VERSION"

# Check manager.py exists
if [ ! -f "$MANAGER_SCRIPT" ]; then
    echo "[✗] manager.py not found at $MANAGER_SCRIPT"
    exit 1
fi
echo "[✓] manager.py: found"

# ── 1. OpenClaw config detection ─────────────────────────────
echo ""
echo "[1/8] Detecting OpenClaw configuration..."
HAS_OPENCLAW_JSON=false
if check_openclaw_json; then
    HAS_OPENCLAW_JSON=true
    AGENT_COUNT=$(python3 -c "import json; d=json.load(open('$OPENCLAW_JSON')); print(len(d.get('agents',{}).get('list',[])))" 2>/dev/null || echo "0")
    echo "  ✓ openclaw.json found ($AGENT_COUNT agent(s))"
else
    echo "  ⚠ openclaw.json not found or invalid — will initialize main agent only"
fi

# ── 2. Create directories ──────────────────────────────────────
echo ""
echo "[2/8] Creating .learnings directories..."

init_agent_learnings() {
    local agent_id=$1
    local workspace=$2
    local learnings_dir="${workspace}/.learnings"

    mkdir -p "$learnings_dir"
    mkdir -p "$learnings_dir/archive"

    # Copy learn.jsonl.example if learn.jsonl doesn't exist
    if [ ! -f "$learnings_dir/learn.jsonl" ]; then
        if [ -f "$LEARN_TEMPLATE" ]; then
            cp "$LEARN_TEMPLATE" "$learnings_dir/learn.jsonl"
        fi
    fi

    echo "    ✓ $agent_id: $learnings_dir"
}

if [ "$HAS_OPENCLAW_JSON" = true ]; then
    load_agent_workspaces | while IFS=: read -r agent_id workspace; do
        init_agent_learnings "$agent_id" "$workspace"
    done
else
    # Fallback: main agent only
    init_agent_learnings "main" "$WORKSPACE"
fi

# ── 3. Install hook ────────────────────────────────────────────
echo ""
echo "[3/8] Installing hook..."
mkdir -p "$CANONICAL_HOOKS"
cp "$SKILL_HOOKS/handler.js" "$CANONICAL_HOOKS/handler.js"
cp "$SKILL_HOOKS/HOOK.md" "$CANONICAL_HOOKS/HOOK.md"
echo "  ✓ handler.js + HOOK.md → $CANONICAL_HOOKS/"

# ── 4. Register hook ──────────────────────────────────────────
echo ""
echo "[4/8] Registering hook..."
if openclaw hooks set self-improvement "$CANONICAL_HOOKS/handler.js" 2>/dev/null; then
    echo "  ✓ Hook registered"
else
    echo "  ⚠ Hook registration may have failed. Run manually if needed:"
    echo "    openclaw hooks set self-improvement $CANONICAL_HOOKS/handler.js"
fi

# ── 5. Restart gateway ─────────────────────────────────────────
echo ""
echo "[5/8] Restarting gateway..."
if openclaw gateway restart 2>/dev/null; then
    echo "  ✓ Gateway restarted"
else
    echo "  ⚠ Gateway restart failed. Please restart manually:"
    echo "    openclaw gateway restart"
fi

# ── 6. Setup crontab (interactive) ─────────────────────────────
echo ""
echo "[6/8] Weekly archive crontab..."
echo "  Should I set up a weekly archive cron job (every Sunday 03:00)?"
echo "  This archives resolved entries from learn.jsonl to monthly files."
echo -n "  [Y/n]: "
read -r response
response="${response:-Y}"
if [[ "$response" =~ ^[Yy]$ ]]; then
    AGENTS_INFO=$(load_agent_workspaces 2>/dev/null || echo "main:$WORKSPACE")
    echo "  Setting up crontab for:"
    echo "$AGENTS_INFO" | while IFS=: read -r agent_id workspace; do
        echo "    - $agent_id: $workspace/.learnings"
    done

    # Build cron entry
    CRON_CMD="0 3 * * 0"
    CRON_WORKSPACE="$WORKSPACE"
    CRON_FULL_CMD="LEARNINGS_DIR=\"$CRON_WORKSPACE/.learnings\" python3 \"$MANAGER_SCRIPT\" archive >> /dev/null 2>&1"

    # Add to crontab (append if not exists)
    (crontab -l 2>/dev/null | grep -v "self-improvement-loop"; echo "$CRON_CMD $CRON_FULL_CMD") | crontab -
    echo "  ✓ Crontab updated"
else
    echo "  Skipped. To set up manually later:"
    echo "    echo '0 3 * * 0 LEARNINGS_DIR=\"~/.openclaw/workspace/.learnings\" python3 \"$MANAGER_SCRIPT\" archive' | crontab -"
fi

# ── 7. Run verification ─────────────────────────────────────────
echo ""
echo "[7/8] Running verification..."

VERIFICATION_FAILED=0

verify_agent() {
    local agent_id=$1
    local learnings_dir="${2}/.learnings"

    echo "  $agent_id:"
    # Check directory exists
    if [ -d "$learnings_dir" ]; then
        echo "    ✓ .learnings/ directory exists"
    else
        echo "    ✗ .learnings/ directory missing"
        VERIFICATION_FAILED=1
        return
    fi

    # Check learn.jsonl
    if [ -f "$learnings_dir/learn.jsonl" ]; then
        ENTRY_COUNT=$(wc -l < "$learnings_dir/learn.jsonl" 2>/dev/null || echo 0)
        echo "    ✓ learn.jsonl exists ($ENTRY_COUNT entries)"
    else
        echo "    ✗ learn.jsonl missing"
        VERIFICATION_FAILED=1
    fi

    # Check manager.py works
    RESULT=$(echo '{"command":"state","action":"get"}' | run_manager "$learnings_dir" 2>/dev/null)
    if [ -n "$RESULT" ]; then
        echo "    ✓ manager.py responds"
    else
        echo "    ✗ manager.py not responding"
        VERIFICATION_FAILED=1
    fi
}

if [ "$HAS_OPENCLAW_JSON" = true ]; then
    load_agent_workspaces | while IFS=: read -r agent_id workspace; do
        verify_agent "$agent_id" "$workspace"
    done
else
    verify_agent "main" "$WORKSPACE"
fi

# ── 8. Done ─────────────────────────────────────────────────────
echo ""
echo "[8/8] Final instructions..."
echo ""
if [ $VERIFICATION_FAILED -eq 0 ]; then
    echo "=== Installation complete ==="
else
    echo "=== Installation complete (with warnings) ==="
fi
echo ""
echo "Next steps:"
echo "  1. The hook will automatically capture corrections, errors, and feature requests"
echo "  2. Run 'manager.py add' to manually log a learning"
echo "  3. Check logs with: openclaw logs | grep self-improvement"
echo ""
echo "Version: v5.0.0"