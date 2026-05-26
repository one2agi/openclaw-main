# 博客配置速查 — 星辰参考

## Notion 数据源

| 项目 | 值 |
|------|---|
| 博客 Page ID | `86f4f4cfc8e28204962a81fbd8aa8916` |
| MCP 工具 | `notion__API-retrieve-a-page`, `notion__API-get-block-children` |

## 文件路径

```
/mnt/d/workspace/notionnext/myNotionNext/
├── blog.config.js                  ← 全局配置（含 NOTION_PAGE_ID）
├── themes/starter/config.js        ← starter 主题文案
├── themes/starter/conf/*.config    ← 进阶配置
└── .git/                           ← Git 仓库
```

## 常用 Git 命令

```bash
cd /mnt/d/workspace/notionnext/myNotionNext
git status
git log --oneline -5
git diff
git add . && git commit -m "[博客] <描述>" && git push
```

## Vercel 命令

```bash
vercel ls                              # 查看部署列表
vercel deploy --prebuilt              # 触发部署（在仓库目录）
vercel rollback <url>                 # 回滚（需目标 URL）
```

## 健康检查

```bash
curl -I https://faiz-world.com
# 期望：HTTP 200
```

---

_星辰 · 2026-05-01_