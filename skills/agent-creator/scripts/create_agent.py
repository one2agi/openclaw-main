#!/usr/bin/env python3
"""
Agent Creator Script
Usage: python3 create_agent.py <agent-name> <agent-id> [bot-token]
"""

import json
import os
import sys
import subprocess

def get_workspace():
    """Detect workspace dynamically"""
    # Try environment variable first
    ws = os.environ.get('OPENCLAW_WORKSPACE')
    if ws and os.path.exists(ws):
        return ws
    
    # Try standard location
    home = os.path.expanduser("~")
    ws = os.path.join(home, ".openclaw", "workspace")
    if os.path.exists(ws):
        return ws
    
    # Use current working directory as fallback
    return os.getcwd()

def create_agent(name, agent_id, bot_token=None):
    workspace = get_workspace()
    base_path = f"{workspace}/agents/{name}"
    
    # Create directories
    dirs = [
        base_path,
        f"{base_path}/.learnings",
        f"{base_path}/memory/projects",
        f"{base_path}/skills"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Create SOUL.md
    soul = f"""# SOUL.md — {name}

**我是{name}，faiz团队的成员。**

## 我是谁

- **名字**：{name}
- **角色**：待定
- **上级**：墨染（军师）
- **Emoji**：🔧

## 核心价值观

1. 目标导向
2. 诚实评估自己的能力边界
3. 主动汇报

## 底线

- 不确认不动手
- 不带目标地收集信息
"""
    with open(f"{base_path}/SOUL.md", "w") as f:
        f.write(soul)
    
    # Create IDENTITY.md
    identity = f"""# IDENTITY.md

- **名字**：{name}
- **本质**：待定
- **Emoji**：🔧
"""
    with open(f"{base_path}/IDENTITY.md", "w") as f:
        f.write(identity)
    
    # Create AGENTS.md
    agents = f"""# AGENTS.md — {name} 运营手册

## 红线（必须遵守）

- 不在 workspace 里放密钥
- 不确认不动手
- 不带目标地收集信息

## Session 启动

1. 读 SOUL.md
2. 读 MEMORY.md
3. 读 AGENTS.md

## 核心职责

待定

## 与墨染的关系

- 只接收墨染的任务
- 任务完成，汇报结果
"""
    with open(f"{base_path}/AGENTS.md", "w") as f:
        f.write(agents)
    
    # Create placeholder files
    for fname in ["MEMORY.md", "HEARTBEAT.md", "TOOLS.md", "USER.md"]:
        path = f"{base_path}/{fname}"
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("")
    
    for fname in ["LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"]:
        path = f"{base_path}/.learnings/{fname}"
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("")
    
    # Update openclaw.json
    config_path = os.path.join(os.path.dirname(workspace), "openclaw.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Add agent
        agents_list = config.get("agents", {}).get("list", [])
        existing = [a for a in agents_list if a.get("id") == agent_id]
        if not existing:
            agents_list.append({
                "id": agent_id,
                "workspace": base_path,
                "model": "minimax/minimax-2.7"
            })
        
        # Add binding if bot token provided
        if bot_token:
            account_id = name.lower().replace(" ", "-")
            accounts = config.get("channels", {}).get("telegram", {}).get("accounts", {})
            if account_id not in accounts:
                accounts[account_id] = {
                    "botToken": bot_token,
                    "dmPolicy": "allowlist",
                    "allowFrom": ["7754385134"]
                }
            
            bindings = config.get("bindings", [])
            binding_exists = any(b.get("agentId") == agent_id for b in bindings)
            if not binding_exists:
                bindings.append({
                    "match": {"channel": "telegram", "accountId": account_id},
                    "agentId": agent_id
                })
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Agent '{name}' created at {base_path}")
    print(f"   Agent ID: {agent_id}")
    if bot_token:
        print(f"   Telegram bot token: configured")
    print("\n⚠️  Restart gateway to activate: openclaw gateway restart")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 create_agent.py <name> <agent-id> [bot-token]")
        sys.exit(1)
    
    name = sys.argv[1]
    agent_id = sys.argv[2]
    bot_token = sys.argv[3] if len(sys.argv) > 3 else None
    
    create_agent(name, agent_id, bot_token)
