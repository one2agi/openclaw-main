# Notion MCP Skill

> 2026-04-27 · 墨染 · 更新 2026-05-01

## Token

`${NOTION_TOKEN}`
位置：`~/.openclaw/openclaw.json` → `mcp.servers.notion.env.NOTION_TOKEN`

## MCP 工具

直接用 `notion__*` 工具，无额外配置。
MCP v2（`@notionhq/notion-mcp-server@latest`）使用 `Notion-Version: 2025-09-03`，正常工作。

## data_source_id 映射（MCP v2 必须用这个）

> ⚠️ MCP v2 工具（如 `query-data-source`）需要 `data_source_id`，不是旧的 `database_id`。

| 数据库 | database_id（旧的） | data_source_id（MCP v2 用这个） |
|--------|-------------------|-------------------------------|
| 手写笔记 | `1994f4cf-c8e2-83e4-8219-81264ed99c29` | `0b34f4cf-c8e2-8383-840f-87946b7b821c` |
| 资源 | `a334f4cf-c8e2-8328-bf6b-01f696885b8f` | `b4a4f4cf-c8e2-8348-9f99-07ff23b401bc` |
| 项目管理器 | `c2d4f4cf-c8e2-82d3-baf4-8175e3e4490a` | `3674f4cf-c8e2-8252-ba79-074460dcdc9d` |

详情：`notion-topic-search.md`

## 数据库文档（按层）

| 层 | 文档 |
|----|------|
| Layer 1 · 执行核心 | `layers/layer-1-execution.md` |
| Layer 2 · 复盘闭环 | `layers/layer-2-review.md` |
| Layer 3 · 知识沉淀 | `layers/layer-3-knowledge.md` |
| Layer 4 · 生活 | `layers/layer-4-life.md` |

## 专题笔记搜索

| 文档 |
|------|
| 按专题名查找笔记/资源 | `notion-topic-search.md` |

## 跨层基础设施（游戏化 + 时间）

游戏化积分：`积分设置` `任务积分设置` `里程碑积分设置` `目标积分设置` `资源积分设置` `笔记积分设置` `日志积分设置` `每日活动记录` `奖励兑换`
时间维度：`日` `周` `月` `年`

---

_墨染 · 2026-04-27 · 更新 2026-05-01_
