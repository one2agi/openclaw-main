#!/bin/bash
# inject_review.sh — v5.0.0
# 输出 JSON 模板供 Agent 填充后调用 manager.py add

LEARNINGS_DIR="${LEARNINGS_DIR:-$(pwd)/.learnings}"
MANAGER_PY="$(cd "$(dirname "$0")" && pwd)/manager.py"

python3 << 'PYEOF'
import json, datetime, os

# 生成当天日期用于 ID 预测
today = datetime.datetime.now().strftime('%Y%m%d')

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

# 输出 JSON 模板和说明
print(json.dumps(template, ensure_ascii=False, indent=2))
PYEOF

cat << 'USAGE'

# 使用方法：
# 1. 填充上面的 JSON 模板
# 2. 保存到临时文件，如 /tmp/review.json
# 3. 执行：
#    python3 scripts/manager.py add --json /tmp/review.json --learnings-dir ~/.openclaw/workspace/agents/{agent}/.learnings

USAGE
