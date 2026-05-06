# MEMORY.md — HOT 层（始终加载）

---

## 已确认的用户偏好

- **WSL2 操作**：apt 装库后需 `sudo ldconfig` 刷新缓存；不自行 systemctl restart
- **WSL2 ↔ Windows 网络**：WSL2 NAT 模式，Windows 宿主机 IP 为 172.20.112.1，VcXsrv X Server 监听 6000 端口，DISPLAY 需设为 `172.20.112.1:0`
- **MoltBook 养号核心公式与策略**
  - 公式：`Karma = (原创帖×质量) + (评论×互动率) + (点赞×回访率)`
  - 策略：热帖30分钟内评论抢可见性；每6小时一轮互动（回5帖+赞10帖）；评论要有实质观点
  - 教训：新账号+推销内容=高spam风险；先积累真实互动再发推销帖

- **博客运营策略**：方案A（信任先行，内容驱动）
  - 定位：AI时代超级个体的成长手册，知行合一是作品证明
  - Notion API 已连接（MCP 本地模式），token 存于 openclaw.json
  - 知行合一数据库 data_source_id 已记录（见 notion-mcp skill）

- **沙盒限制**：sub-agent 沙盒拒绝访问 workspace 外的路径；isolated session 无 exec 权限（`toolsAllow: ["exec"]` 可用）；详见 `self-improving/domains/openclaw.md`
- **Chrome 路径**：`/tmp/chrome-extract/opt/google/chrome/chrome`
- **Notion MCP**：本地 `npx @notionhq/notion-mcp-server` 已配置；读写均可用 MCP 工具，**三库 data_source_id**：手写笔记 `0b34f4cf-c8e2-8383-840f-87946b7b821c` / 资源 `b4a4f4cf-c8e2-8348-9f99-07ff23b401bc` / 项目管理器 `3674f4cf-c8e2-8252-ba79-074460dcdc9d`
- **Notion Skill**：`skills/notion-mcp/SKILL.md`

---

## 项目文件位置（快速索引）

> 项目详情（进展、Blockers、Next Actions）统一在对应路径下，MEMORY.md 只做索引。

| 项目 | 路径 |
|------|------|
| 知行合一商业化 | `memory/projects/zhi-xing-he-yi.md` |
| 博客运营 | `memory/projects/notionnext-blog.md` |
| 自我进化闭环 | `self-improving/` |
| MoltBook 养号 | `self-improving/domains/moltbook.md` |
| OpenClaw 配置 | `self-improving/domains/openclaw.md` |
| 网络问题 | `network/NETWORK_ISSUES.md` |

---

## 代理团队架构

- **技术部门只有 无极 + CC** — 不再使用其他 sub-agent 处理代码任务
- 无极 = 技术负责人（架构、决策、审核）
- CC (Claude Code) = 超级码农（具体编码执行）
- 工作流：faiz → 墨染 → 无极 → CC → 无极审核 → 交付

## 市场研究 Skill 选择指南
- **market-research（ivan）** → 报告需要数字/百分比时用，侧重真实性、量化数据
- **market-research-agent（1ka）** → 报告需要快速、结构化、有摘要时用，侧重速度和呈现

## 报告集中仓库
- 仓库：jichangtuijie/ai-workforce-report
- GitHub Pages：https://jichangtuijie.github.io/ai-workforce-report/

---

## 经验索引

| 类型 | 路径 |
|------|------|
| learnings | `.learnings/LEARNINGS.md` |
| errors | `.learnings/ERRORS.md` |
| feature requests | `.learnings/FEATURE_REQUESTS.md` |

---

## 教训索引
| 类别 | 教训数 | 最新更新 |
|------|--------|----------|
| corrections | 1 | 2026-04-19 |
| best_practices | 2 | 2026-04-27 |
| insights | 0 | — |
| errors | 1 | 2026-04-01 |

*Last updated: 2026-04-27*