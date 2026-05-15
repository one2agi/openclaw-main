---
name: xianyu-plugin
description: 闲鱼插件工具包。当需要与闲鱼交互时使用此 skill，包括：查询账号状态、获取消息、发送消息、发布商品、管理发货规则、处理验证码等。触发词："闲鱼"、"咸鱼"、"xianyu"。
---

# xianyu-plugin

闲鱼 OpenClaw 插件的接口封装，提供闲鱼业务的完整工具调用能力。

## 前提条件

**必须先启动 xianyu 服务**，否则所有接口不可用。

服务地址：`http://192.168.31.60:9090`

启动命令：
```bash
cd /mnt/d/project/xianyu/xianyu-openclaw-channel && python3 Start.py
```

等待约 10 秒后验证：
```bash
curl http://192.168.31.60:9090/health
```

## 启动检测

每次调用接口前，先检测服务是否在线：
```bash
curl -s --connect-timeout 3 http://192.168.31.60:9090/health
```

若返回 `{"status":"healthy"}` 表示服务正常，否则先启动服务。

## 工具函数

所有接口均通过 `exec` + `curl` 调用。

### 健康检查

```bash
curl http://192.168.31.60:9090/health
```

### 查询状态

```bash
curl -s http://192.168.31.60:9090/api/bridge/status
```

返回：
```json
{
  "running": true,
  "activeConnections": 1,
  "messageQueueSize": 0,
  "accounts": [...]
}
```

### 查询账号列表

```bash
curl -s http://192.168.31.60:9090/api/bridge/accounts
```

### 获取消息（长轮询 SSE）

```bash
curl -s http://192.168.31.60:9090/api/bridge/messages?accountId=<账号ID>&lastEventId=<上次ID>
```

### 发送消息

```bash
curl -s -X POST http://192.168.31.60:9090/api/bridge/send \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "<账号ID>",
    "conversationId": "<会话ID>",
    "content": "<消息内容>",
    "tempToken": "<临时token>"
  }'
```

### 确认收货

```bash
curl -s -X POST http://192.168.31.60:9090/api/bridge/confirm-delivery \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "<账号ID>",
    "orderId": "<订单ID>"
  }'
```

### 刷新 Cookie

```bash
curl -s -X POST http://192.168.31.60:9090/api/bridge/refresh-cookie \
  -H "Content-Type: application/json" \
  -d '{"accountId": "<账号ID>"}'
```

### 查询商品列表

```bash
curl -s "http://192.168.31.60:9090/api/bridge/products?accountId=<账号ID>"
```

### 发布单个商品

```bash
curl -s -X POST http://192.168.31.60:9090/api/bridge/publish/single \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_id": "<账号cookie_id>",
    "title": "<商品标题>",
    "description": "<商品描述>",
    "price": <价格>,
    "images": ["<图片URL>", ...],
    "category": "<分类ID>"
  }'
```

### 批量发布商品

```bash
curl -s -X POST http://192.168.31.60:9090/api/bridge/publish/batch \
  -H "Content-Type: application/json" \
  -d '{
    "cookie_id": "<账号cookie_id>",
    "products": [
      {"title": "...", "description": "...", "price": 20, "images": [], "category": ""},
      ...
    ]
  }'
```

### 发货规则

```bash
# 查询
curl -s "http://192.168.31.60:9090/api/bridge/delivery-rules?accountId=<账号ID>"

# 设置
curl -s -X POST http://192.168.31.60:9090/api/bridge/delivery-rules \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "<账号ID>",
    "autoDelivery": true,
    "location": "<发货地>"
  }'
```

## 验证码处理

通过 WebSocket 远程控制验证码：

```bash
# 获取活动会话
curl -s http://192.168.31.60:9090/api/captcha/sessions

# 获取会话截图
curl -s "http://192.168.31.60:9090/api/captcha/screenshot/<session_id>"
```

验证码控制台：`http://192.168.31.60:9090/api/captcha/control`

## API 参考

详细接口规范见 `references/api_reference.md`