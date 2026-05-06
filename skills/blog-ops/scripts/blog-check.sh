#!/bin/bash
# 博客巡检脚本（星辰专用）
# 用法：./blog-check.sh

BLOG_DIR="/mnt/d/workspace/notionnext/myNotionNext"

echo "=== 博客巡检 ==="
echo ""

echo "[1/5] Git 状态"
cd "$BLOG_DIR" && git status --short
echo ""

echo "[2/5] 最近提交"
cd "$BLOG_DIR" && git log --oneline -3
echo ""

echo "[3/5] Vercel 部署"
vercel ls 2>/dev/null || echo "vercel CLI 未找到"
echo ""

echo "[4/5] 博客访问"
curl -s -o /dev/null -w "HTTP %{http_code}" https://faiz-world.com || echo "无法连接"
echo ""

echo "[5/5] Page ID 确认"
cd "$BLOG_DIR" && grep "NOTION_PAGE_ID" blog.config.js || echo "未找到配置"
echo ""

echo "=== 巡检完毕 ==="