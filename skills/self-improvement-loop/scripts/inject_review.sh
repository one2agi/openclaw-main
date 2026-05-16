#!/bin/bash
# inject_review.sh — Generate structured self-review prompt
# v1.0.0
# Usage: inject_review.sh <learnings_dir>

set -euo pipefail

LEARNINGS_DIR="${1:-}"

if [ -z "$LEARNINGS_DIR" ]; then
    echo "Usage: inject_review.sh <learnings_dir>" >&2
    exit 1
fi

# Read learnings_dir from argument, substitute into prompt
python3 -c "
import sys
ld = sys.argv[1] if len(sys.argv) > 1 else ''
prompt = '''
## 🪞 Self-Review — 任务回顾

你刚刚完成了一段复杂交互（消息数达到阈值）。现在请回顾这次工作：

### 1. 这次用了什么方法/步骤？
（描述你解决问题的主要思路和操作序列）

### 2. 有没有坑点或绕弯的地方？
（记录遇到的错误、挫折、或不高效的地方）

### 3. 下次遇到类似任务，怎么做更好？
（提炼一条可复用的原则）

### 4. 有没有值得写成技能/规则的内容？

---

**记录到 learnings 文件**（选择合适的一个）：
- 洞察/最佳实践 → ''' + ld + '''/LEARNINGS.md
- 命令/工具失败 → ''' + ld + '''/ERRORS.md
- 功能缺失需求 → ''' + ld + '''/FEATURE_REQUESTS.md

参考模板格式（8-27行）：ID用 \`YYYYMMDD-NNN\`，Status填 \`pending\`，Pattern-Key 用 \`<source>.<type>.<identifier>\` 格式。

如果值得记录技能，请用 A/B/C/D 标记：
- **A** = 创建新技能（用于可复用的完整工作流）
- **B** = 优化现有技能
- **C** = 跳过（这次不够通用）
- **D** = 升华到 SOUL/AGENTS/TOOLS（用于行为规则/工作流/工具坑点）
'''
print(prompt)
" \"$LEARNINGS_DIR\"