#!/bin/bash
# skill-scan.sh - 双重安全扫描（skill-security-auditor + clawned）
# 用法: ./skill-scan.sh <skill路径或slug>
# 依赖: jq (已安装在 ~/.local/bin/jq)

export PATH="$HOME/.local/bin:$PATH"
AUDITOR_DIR="$HOME/.openclaw/workspace/skills/skill-security-auditor"

SKILL="$1"
if [ -z "$1" ]; then
  echo "用法: $0 <skill路径或clawhub-slug>"
  exit 1
fi

echo "🔍 双重安全扫描: $SKILL"
echo "========================================"

# 1. skill-security-auditor（本地模式，20+ 威胁模式）
echo ""
echo "【Scanner 1: skill-security-auditor】"
if [ -f "$AUDITOR_DIR/analyze-skill.sh" ]; then
  if [[ "$SKILL" == *".md"* ]] || [ -d "$SKILL" ]; then
    TARGET="$SKILL"
    [ -d "$TARGET" ] && TARGET="$TARGET/SKILL.md"
    bash "$AUDITOR_DIR/analyze-skill.sh" -f "$TARGET" 2>&1 | grep -E "Risk Score|RECOMMENDATION|No security|security concerns|detected|✅|⚠️"
  else
    bash "$AUDITOR_DIR/analyze-skill.sh" -s "$SKILL" 2>&1 | grep -E "Risk Score|RECOMMENDATION|No security|security concerns|detected|✅|⚠️"
  fi
else
  echo "⚠️ skill-security-auditor 未安装"
fi

echo ""
echo "【Scanner 2: Clawned（需 API Key）】"
echo "→ https://clawned.io 获取 API Key 后可启用云端扫描"
echo "→ 或访问 https://clawhub.io 查看技能的安全标签"

echo ""
echo "========================================"
echo "📋 结果已生成，可疑项目已高亮"
