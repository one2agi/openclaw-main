#!/usr/bin/env python3
"""
Session Cleanup — 清理 7 天未活动的 subagent 会话
- 从 sessions.json 中移除旧条目
- 删除对应的 transcript .jsonl 文件
- 保留 cron / direct 会话
"""
import json, os, time, sys
from pathlib import Path

AGE_DAYS = int(os.environ.get("SESSION_CLEANUP_DAYS", "7"))
AGE_SECONDS = AGE_DAYS * 86400
DRY_RUN = "--dry-run" in sys.argv

agents = os.environ.get("SESSION_CLEANUP_AGENTS", "main,claude,code-dev,moling,xingchen").split(",")
now = time.time()
total_removed = 0

for agent in agents:
    base = Path.home() / ".openclaw" / "agents" / agent / "sessions"
    json_path = base / "sessions.json"
    if not json_path.exists():
        continue

    with open(json_path) as f:
        data = json.load(f)

    to_remove_keys = []
    to_remove_files = []

    for k, v in data.items():
        # 只清理 subagent
        if "subagent" not in k:
            continue
        updated = v.get("updatedAt", 0) / 1000
        age = now - updated
        if age > AGE_SECONDS:
            to_remove_keys.append(k)
            # 清理 transcript 文件
            sid = v.get("sessionId")
            if sid:
                transcript = base / f"{sid}.jsonl"
                if transcript.exists():
                    to_remove_files.append(transcript)

    if not to_remove_keys:
        continue

    if DRY_RUN:
        print(f"\n[{agent}] DRY RUN — 会删除 {len(to_remove_keys)} 个 subagent:")
        for k in to_remove_keys:
            age = (now - data[k].get("updatedAt", 0)/1000) / 86400
            label = data[k].get("label", "")
            print(f"  {age:.1f}d  {k[:65]}  label={label}")
    else:
        for k in to_remove_keys:
            del data[k]
        for f in to_remove_files:
            f.unlink()
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[{agent}] 清理完成：删除 {len(to_remove_keys)} 条目")

    total_removed += len(to_remove_keys)

print(f"\n总清理: {total_removed} 个 subagent 会话 (>{AGE_DAYS}天)")
print(f"模式: {'DRY RUN' if DRY_RUN else 'APPLIED'}")