# 闲鱼插件 API 参考

## 基础信息

- **Base URL**: `http://192.168.31.60:9090`
- **认证**: 通过 Cookie/Token 机制，登录后获取 session
- **数据格式**: JSON

---

## 健康检查

### GET `/health`

服务健康状态。

**响应:**
```json
{
  "status": "healthy",
  "timestamp": 1778815563,
  "services": {
    "cookie_manager": "ok",
    "database": "ok"
  },
  "system": {
    "cpu_percent": 3.3,
    "memory_percent": 22.8,
    "memory_available": 6427336704
  }
}
```

---

## 消息通道 API

### GET `/api/bridge/status`

整体状态。

**响应:**
```json
{
  "running": true,
  "activeConnections": 1,
  "messageQueueSize": 0,
  "accounts": [
    {
      "accountId": "2207836320265",
      "name": "2207836320265",
      "enabled": true,
      "connected": true
    }
  ]
}
```

### GET `/api/bridge/accounts`

账号列表。

**响应:**
```json
{
  "accounts": [
    {
      "accountId": "2207836320265",
      "name": "描述性名称",
      "enabled": true,
      "connected": true
    }
  ]
}
```

### GET `/api/bridge/messages`

SSE 长轮询获取消息。

**参数:**
- `accountId` (required): 账号 ID
- `lastEventId` (optional): 上次接收的事件 ID，用于断点续传

**响应 (SSE):**
```
event: message
data: {"eventId":"xxx","accountId":"2207836320265","type":"chat","content":"买家说了什么","conversationId":"xxx","timestamp":"..."}

event: message
data: {"eventId":"yyy","accountId":"2207836320265","type":"system","content":"xxx","timestamp":"..."}
```

**事件类型:**
- `chat` — 聊天消息
- `system` — 系统通知
- `order` — 订单相关

---

## 发送消息

### POST `/api/bridge/send`

发送文本消息。

**Body:**
```json
{
  "accountId": "2207836320265",
  "conversationId": "会话ID",
  "content": "要发送的文本内容",
  "tempToken": "临时token（可选）"
}
```

**响应:**
```json
{
  "success": true,
  "messageId": "发送的消息ID"
}
```

### POST `/api/bridge/send-media`

发送图片消息。

**Body:**
```json
{
  "accountId": "2207836320265",
  "conversationId": "会话ID",
  "imageUrls": ["https://图片URL"],
  "tempToken": ""
}
```

---

## 商品管理

### GET `/api/bridge/products`

查询账号下的商品列表。

**参数:**
- `accountId` (optional): 账号 ID，不填则查所有

**响应:**
```json
{
  "products": [
    {
      "itemId": "986602727648",
      "title": "商品标题",
      "price": "14",
      "price_text": "¥14",
      "status": "在售",
      "picUrl": "http://图片URL",
      "category_id": 50023914
    }
  ]
}
```

### POST `/api/bridge/publish/single`

发布单个商品。

**Body:**
```json
{
  "cookie_id": "2207836320265",
  "title": "商品标题",
  "description": "商品详情描述",
  "price": 25,
  "images": ["https://图片1.jpg", "https://图片2.jpg"],
  "category": "50023914",
  "original_price": 35,
  "stock": 1,
  "location": "上海"
}
```

**响应:**
```json
{
  "success": true,
  "itemId": "新商品ID",
  "message": "发布成功"
}
```

### POST `/api/bridge/publish/batch`

批量发布。

**Body:**
```json
{
  "cookie_id": "2207836320265",
  "products": [
    {
      "title": "商品1",
      "description": "描述",
      "price": 20,
      "images": [],
      "category": ""
    },
    {
      "title": "商品2",
      "description": "描述",
      "price": 30,
      "images": [],
      "category": ""
    }
  ]
}
```

**响应:**
```json
{
  "success": true,
  "results": [
    {"success": true, "itemId": "商品1ID"},
    {"success": false, "error": "错误信息"}
  ]
}
```

---

## 订单与发货

### POST `/api/bridge/confirm-delivery`

确认收货。

**Body:**
```json
{
  "accountId": "2207836320265",
  "orderId": "订单ID"
}
```

### GET `/api/bridge/delivery-rules`

查询发货规则。

**参数:**
- `accountId` (required): 账号 ID

### POST `/api/bridge/delivery-rules`

设置发货规则。

**Body:**
```json
{
  "accountId": "2207836320265",
  "autoDelivery": true,
  "location": "上海",
  "autoReply": true,
  "replyTemplates": {
    "发货": "您的订单已发货，快递单号：{tracking_no}"
  }
}
```

---

## Cookie 管理

### POST `/api/bridge/refresh-cookie`

刷新指定账号的 Cookie（通过浏览器自动化）。

**Body:**
```json
{
  "accountId": "2207836320265"
}
```

**响应:**
```json
{
  "success": true,
  "message": "Cookie 刷新成功"
}
```

---

## 验证码处理

### GET `/api/captcha/sessions`

获取所有活动验证码会话。

### GET `/api/captcha/session/{session_id}`

获取单个会话详情。

### GET `/api/captcha/screenshot/{session_id}`

获取验证码截图（用于人工辅助识别）。

### POST `/api/captcha/mouse_event`

提交鼠标事件完成验证。

**Body:**
```json
{
  "sessionId": "会话ID",
  "action": "click",
  "x": 100,
  "y": 200
}
```

### DELETE `/api/captcha/session/{session_id}`

关闭验证码会话。

---

## 错误码

| ret code | 说明 |
|----------|------|
| `FAIL_SYS_TOKEN_EXOIRED` | Token 过期，需要刷新 Cookie |
| `FAIL_BIZ_DUPLICATE_ITEM` | 商品重复发布 |
| `FAIL_BIZ_ITEM_NOT_FOUND` | 商品不存在 |
| `FAIL_BIZ_SESSION_EXPIRED` | 会话过期 |

---

## 认证流程

1. 首次使用需要通过 Web UI 登录：`http://192.168.31.60:9090/login`
2. 登录后获取 session token（存在 cookie 中）
3. 后续请求携带 session token 即可