#!/bin/bash
# skill-security-scan.sh
# 用法: ./skill-security-scan.sh <skill路径>
# 输出: 精简威胁报告

SKILL_PATH="$1"
if [ -z "$SKILL_PATH" ]; then
  echo "用法: $0 <skill路径>"
  exit 1
fi

echo "🔍 扫描技能: $SKILL_PATH"
echo "---"

FOUND=()

# 1. 网络可疑请求（未知境外域名）
SUSPICIOUS_DOMAINS=$(grep -rEH "(https?://|http?://)[a-zA-Z0-9.-]+\.(ru|cn|xyz|tk|ml|ga|cf|gq|top|work|click|pw|cc|buzz|site|online|tech|promo|shop|click|link|download|click)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v "#" | grep -v "README")
if [ -n "$SUSPICIOUS_DOMAINS" ]; then
  FOUND+=("🌐 可疑网络请求")
fi

# 2. 凭证/Token 读取
CRED_READS=$(grep -rEH "(process\.env|GITHUB_|TOKEN|API_KEY|SECRET|PASSWORD|PRIVATE_KEY|AUTH_TOKEN|OPENAI_|CLAUDE_|GEMINI_|MINIMAX_)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v "#.*#" | grep -v "example\|sample\|placeholder" | grep -c "." || true)
if [ "$CRED_READS" -gt 0 ]; then
  FOUND+=("🔑 凭证读取（$CRED_READS 处）")
fi

# 3. 动态代码执行（eval, exec, base64 decode, shell执行）
DYNAMIC=$(grep -rEH "(eval\(|exec\(|subprocess|spawn\(|child_process|os\.system|popen|base64\.decode|b64decode|sh -c|bash -c|\| sh|\| bash|\$\(.*\$\)|`.*`)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$DYNAMIC" -gt 0 ]; then
  FOUND+=("⚡ 动态代码执行（$DYNAMIC 处）")
fi

# 4. 文件写入/系统修改
FILE_WRITE=$(grep -rEH "(write_file|create_file|\.write\(|open\(.*[wa]|mv |cp -r |rm -|chmod |sudo |tee |trash )" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$FILE_WRITE" -gt 0 ]; then
  FOUND+=("📁 文件写入/系统修改（$FILE_WRITE 处）")
fi

# 5. 压缩包/远程下载
REMOTE_FETCH=$(grep -rEH "(wget |curl.*-O|fetch\(.*http|\.download|http\.get|http\.post.*https?)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$REMOTE_FETCH" -gt 0 ]; then
  FOUND+=("📡 远程下载（$REMOTE_FETCH 处）")
fi

# 6. 加密/编码混淆
OBFUSCATED=$(grep -rEH "(base64|zlib|gzip|compress|encode|decode|encrypt|decrypt|obfusc)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$OBFUSCATED" -gt 0 ]; then
  FOUND+=("🔒 加密/编码混淆（$OBFUSCATED 处）")
fi

# 7. 提权请求
PRIVILEGE=$(grep -rEH "(sudo|elevated|root|chmod 777|whoami.*root|uid.*0)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$PRIVILEGE" -gt 0 ]; then
  FOUND+=("👤 提权行为（$PRIVILEGE 处）")
fi

# 8. 敏感文件访问
SENSITIVE=$(grep -rEH "(\.ssh|\.aws|\.npmrc|\.netrc|known_hosts|id_rsa|id_ed25519|/etc/passwd|\.env$)" "$SKILL_PATH" 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -c "." || true)
if [ "$SENSITIVE" -gt 0 ]; then
  FOUND+=("🔐 敏感文件访问（$SENSITIVE 处）")
fi

# 汇总
echo ""
if [ ${#FOUND[@]} -eq 0 ]; then
  echo "✅ 未发现明显威胁模式"
else
  echo "⚠️  发现 ${#FOUND[@]} 类风险:"
  for item in "${FOUND[@]}"; do
    echo "  $item"
  done
fi
}
