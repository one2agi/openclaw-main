#!/bin/bash
set -e

echo "=== 清理 self-improvement hooks & crons ==="

# 1. 删除 hook 配置
python3 -c "
import json
d = json.load(open('/home/morav/.openclaw/openclaw.json'))
entries = d.get('hooks', {}).get('internal', {}).get('entries', {})
if 'self-improvement' in entries:
    del entries['self-improvement']
    print('hook config deleted')
json.dump(d, open('/home/morav/.openclaw/openclaw.json', 'w'), indent=2, ensure_ascii=False)
"

# 2. 删除 hook 文件
rm -rf ~/.openclaw/hooks/self-improvement/
echo "hook files deleted"

# 3. 删除 cron jobs
for id in $(openclaw cron list --json 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
for j in d.get('jobs', []):
    if 'self-improvement' in j.get('name',''):
        print(j.get('id',''))
" 2>/dev/null); do
    openclaw cron remove "$id" 2>/dev/null && echo "removed $id" || echo "failed $id"
done

echo ""
echo "=== 运行安装脚本 ==="
bash ~/.openclaw/workspace/skills/self-improvement-loop/install.sh