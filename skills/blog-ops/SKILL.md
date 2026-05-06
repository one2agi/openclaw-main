# blog-ops — 博客运维技能（全局共享版）

> **所属 agent：** 星辰（xingchen）
> **触发条件：** 收到博客运维指令时读取

---

## 核心 SOP

### 推送更新
```
1. cd /mnt/d/workspace/notionnext/myNotionNext && git status
2. git diff --stat
3. git add . && git commit -m "[博客] <描述>"
4. git push
5. vercel deploy --prebuilt（在仓库目录执行）
6. vercel ls
7. curl -I https://faiz-world.com
```

### 部署检查
```
1. vercel ls
2. cd /mnt/d/workspace/notionnext/myNotionNext && git log --oneline -3 && git status
3. curl -I https://faiz-world.com
```

### 巡检
```
1. git status（未推送改动？）
2. 读取 Notion Page `86f4f4cfc8e28204962a81fbd8aa8916`
3. vercel ls
4. curl -I https://faiz-world.com
5. grep NOTION_PAGE_ID blog.config.js
```

### 配置修改
```
1. cat <file>（展示当前内容）
2. cp <file> <file>.bak
3. edit（精确替换）
4. cat <file>（验证）
5. git diff
```

### 回滚
```
1. vercel ls
2. 列出最近 3 个部署（sha / 时间 / 状态）
3. 等确认目标版本
4. vercel rollback <url>
```

---

## 硬性配置

| 项目 | 值 |
|------|---|
| Notion Page ID | `86f4f4cfc8e28204962a81fbd8aa8916` |
| 仓库路径 | `/mnt/d/workspace/notionnext/myNotionNext` |
| 博客地址 | `https://faiz-world.com` |
| 主题 | starter |

---

## 错误处理

| 错误 | 处理 |
|------|------|
| `cd: /mnt/d/... No such file` | 停手，回报「路径不存在」 |
| `git push rejected` | 回报，列冲突详情 |
| `vercel: command not found` | 回报「CLI 未安装」 |
| `NOTION_PAGE_ID mismatch` | 立即停手，回报 |
| `curl: (7) Failed to connect` | 回报「博客不可访问」 |

---

_本技能由墨染创建，星辰专用。操作规范见 AGENTS.md。_