# Notion 专题搜索

> 通过专题名查找该专题下的所有笔记和资源。
> 2026-05-01 · 更新 data_source_id

## 核心数据库

> ⚠️ **MCP v2 需要 data_source_id**。通过 `retrieve-a-database` 查到，旧的 database_id 对应新的 data_source_id：

| 数据库 | database_id（旧的） | data_source_id（MCP v2 用这个） |
|--------|-------------------|-------------------------------|
| 手写笔记 | `1994f4cf-c8e2-83e4-8219-81264ed99c29` | `0b34f4cf-c8e2-8383-840f-87946b7b821c` |
| 资源 | `a334f4cf-c8e2-8328-bf6b-01f696885b8f` | `b4a4f4cf-c8e2-8348-9f99-07ff23b401bc` |
| 项目管理器 | `c2d4f4cf-c8e2-82d3-baf4-8175e3e4490a` | `3674f4cf-c8e2-8252-ba79-074460dcdc9d` |

两个数据库都有 `专题` 字段（relation 类型），可按专题 page_id 过滤。

## Step 1：找专题 page_id

```bash
TOPIC="专题名称"
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$TOPIC\", \"filter\": {\"property\": \"object\", \"value\": \"page\"}}" \
  | python3 -c "
import json,sys
data = json.load(sys.stdin)
for item in data.get('results',[]):
    title = ''.join([r.get('plain_text','') for r in item.get('properties',{}).get('title',{}).get('title',[])]) or 'no title'
    print(f'ID: {item[\"id\"]} | {title}')
"
```

输出中的 `ID` 即为专题 page_id（格式：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）。

## Step 2：查该专题下的笔记

用 `notion__API-query-data-source` 工具，`data_source_id` 填 `0b34f4cf-c8e2-8383-840f-87946b7b821c`。

filter 示例：
```json
{"property": "专题", "relation": {"contains": "专题page_id"}}
```

## Step 3：查该专题下的资源

用 `notion__API-query-data-source` 工具，`data_source_id` 填 `b4a4f4cf-c8e2-8348-9f99-07ff23b401bc`。

## 快速验证

```bash
# 查找"自我认知与复盘"专题下的全部内容
TOPIC_ID="1054f4cf-c8e2-8248-9219-01aac1657d8e"

# 笔记（data_source_id=0b34...）
notion__API-query-data-source --data_source_id "0b34f4cf-c8e2-8383-840f-87946b7b821c" \
  --filter "{\"property\":\"专题\",\"relation\":{\"contains\":\"$TOPIC_ID\"}}"

# 资源（data_source_id=b4a4...）
notion__API-query-data-source --data_source_id "b4a4f4cf-c8e2-8348-9f99-07ff23b401bc" \
  --filter "{\"property\":\"专题\",\"relation\":{\"contains\":\"$TOPIC_ID\"}}"
```

## 常见坑

- **data_source_id ≠ database_id**：MCP v2 用 data_source_id（以 `0b34`, `b4a4`, `3674` 开头），不能用旧的 database_id（以 `1994`, `a334`, `c2d4` 开头）。查错了会 `object_not_found`。
- **inline database**（子数据库）的 block_id ≠ database_id，直接查 `/databases/{block_id}` 会 404
- **relation filter** 要用 `contains` 而非 `equals`（contains 匹配 page_id 即可）
- `NOTION_TOKEN` 从 `openclaw.json` 的 `mcp.servers.notion.env.NOTION_TOKEN` 读取
