#!/bin/bash
# cron_runner.sh — self-improvement-loop v5.0.0
# Per-agent cron 执行器：scan → notify → archive
set -e

AGENT_ID="${1:-main}"
WORKSPACE="${HOME}/.openclaw/workspace"
MANAGER_PY="$(cd "$(dirname "$0")" && pwd)/manager.py"
LEARNINGS_DIR="$WORKSPACE/agents/$AGENT_ID/.learnings"

export LEARNINGS_DIR
START_TIME=$(date '+%s')

# ── LEARNINGS_DIR validation ─────────────────────────────
if [ ! -d "$LEARNINGS_DIR" ]; then
    echo "[$AGENT_ID] FATAL: LEARNINGS_DIR does not exist: $LEARNINGS_DIR" >&2
    exit 1
fi

# ── Configurable threshold ────────────────────────────────
SCAN_THRESHOLD="${SCAN_THRESHOLD:-2}"

# ── Scan patterns ───────────────────────────────────────
SCAN_RESULT=$(python3 "$MANAGER_PY" scan --threshold "$SCAN_THRESHOLD" --trigger-only 2>&1)

if [ -z "$SCAN_RESULT" ]; then
    echo "[$AGENT_ID] scan failed or empty" >&2
    exit 1
fi

# ── Check if should notify ───────────────────────────────
SHOULD=$(echo "$SCAN_RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    patterns = d.get('patterns', [])
    should = any(p.get('should_notify', False) for p in patterns)
    print('true' if should else 'false')
except Exception as e:
    print(f'parse error: {e}', file=sys.stderr)
    print('false')
")

if [ "$SHOULD" = "true" ]; then
    # 通知逻辑（由 channel bot 处理）
    # 这里只标记已通知
    if ! echo "$SCAN_RESULT" | python3 -c "
import sys, json, subprocess
try:
    d = json.load(sys.stdin)
    manager = '$MANAGER_PY'
    for p in d.get('patterns', []):
        if p.get('should_notify'):
            entry_id = p['first_entry']['id']
            result = subprocess.run(['python3', manager, 'notify', entry_id], capture_output=True, text=True)
            if result.returncode != 0:
                print(f'notify {entry_id} failed: {result.stderr}', file=sys.stderr)
                sys.exit(1)
except Exception as e:
    print(f'notify error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1; then
        echo "[$AGENT_ID] notify failed, will retry next run" >&2
    fi
fi

# ── Archive resolved entries ──────────────────────────────
ARCHIVE_DRY=$(python3 "$MANAGER_PY" archive --dry-run 2>&1)
if echo "$ARCHIVE_DRY" | grep -q "Would archive"; then
    if ! python3 "$MANAGER_PY" archive 2>&1; then
        echo "[$AGENT_ID] archive failed, will retry next run" >&2
    fi
fi

END_TIME=$(date '+%s')
DURATION=$((END_TIME - START_TIME))
echo "[$AGENT_ID] cron completed at $(date '+%Y-%m-%d %H:%M:%S') (took ${DURATION}s)"