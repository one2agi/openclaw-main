# Android 语音 + AI 交互方案调研

> 调研时间：2026-04-10
> 背景：faiz 想把 OpenClaw（墨染 Moran）变成手机上的语音助手，替代小爱同学
> 需求方：faiz（独立创作者，Notion/AI/Nocode 玩家）

---

## 一、Android 语音触发 + AI 交互的现有方案（2025-2026）

### 1.1 端侧唤醒词 + 云端 AI（推荐主流路线）

**核心架构：唤醒词检测 → STT → LLM → TTS**

| 方案 | 特点 | 价格 | 平台 |
|------|------|------|------|
| **Picovoice** | 全部端侧（唤醒词+STT+LLM+TTS），企业级，已大规模部署 | 企业定价，个人免费有限额 | iOS/Android/Web/嵌入式 |
| **DAVoice** | 低 CPU、隐私优先，唤醒词/VAD/STTS/TTS/声纹识别 | 开发者定价 | iOS/Android/Web/Python |
| **Spokestack** | ML 语音方案，唤醒词+关键词识别+ASR+NLU+TTS | 开源免费 / 企业订阅 | iOS/Android/Web |
| **OpenWakeWord** | 开源自定义唤醒词训练工具，配合 HA/Rhasspy 使用 | 完全免费开源 | 配合 HA 使用 |
| **Ayega** (GitHub) | 开源 Android App，允许自定义唤醒词激活语音助手 | 完全免费开源 | Android |

### 1.2 典型技术栈组合

**方案 A：全本地（最高隐私）**
```
Ayega（唤醒词检测）
  → Rhasspy（本地 STT + NLU）
  → 本地 LLM（如 Ollama）
  → Rhasspy（本地 TTS）
```

**方案 B：半本地（推荐性价比）**
```
Hotword Plugin（唤醒词）
  → Tasker（触发 + HTTP 请求）
  → OpenClaw API（LLM 处理）
  → 系统 TTS 播报
```

**方案 C：全云端（最简单）**
```
系统语音助手触发（如小爱/Google Assistant）
  → webhook / IFTTT
  → OpenClaw（Telegram Bot）
  → Telegram 语音回复
```

### 1.3 特别值得关注

- **Home Assistant 生态**：HAwake App 将任何 Android 设备变成带唤醒词的私有语音界面，配合 Home Assistant Companion App + Assist 服务使用
- **Hotwork Plugin**：配合 Tasker 实现唤醒词检测触发
- **Snowboy**：经典开源唤醒词检测库，已停止维护但仍有参考价值，OpenWakeWord 是其精神继承者

---

## 二、Tasker 语音方案替代品

### 2.1 核心替代品对比

| 应用 | 价格 | 语音能力 | 难度 |
|------|------|----------|------|
| **Tasker** | 买断 $3.49（官网）| ★★★★★ 最强大，语音触发/变量/HTTP全支持 | 高 |
| **MacroDroid** | 免费有限/买断 $4.49 | ★★★★ 支持语音触发、HTTP请求，比 Tasker 简单 | 中 |
| **Automate** (LlamaLab) | 免费有限/高级订阅 | ★★★ 流程图界面，语音触发需插件 | 低 |
| **Easer** | 开源免费 | ★★ 基础自动化，轻量 | 中 |
| **IFTTT** | 免费有限/订阅 | ★★ 简单语音触发（Alexa/Google），但灵活性低 | 低 |

### 2.2 结论

- **最推荐**：**MacroDroid**（买断 $4.49，便宜，语音触发 + HTTP 请求够用）
- **最强推荐**：**Tasker**（$3.49 买断，一次付费，终身使用，语音能力最完整）
- 两者都支持通过 HTTP 请求调用外部 API（如 OpenClaw/Telegram Bot）

---

## 三、国内品牌手机语音助手第三方接入方式

### 3.1 现状总结

| 品牌 | 助手 | 官方 API | 第三方接入 | 风险 |
|------|------|----------|-----------|------|
| 小米 | 小爱同学 | ❌ 无公开 API | Root + Xposed 模块 | 高 |
| 华为 | 鸿蒙小艺 | ❌ 无公开 API | HarmonyOS 原子化服务（受限） | 高 |
| OPPO | 小布助手 | ❌ 无公开 API | 无 | — |
| Vivo | Jovi | ❌ 无公开 API | 无 | — |

### 3.2 实际可行方案

**① 绕过官方 API 的间接方案**
- 通过 **Intent 广播 / Accessibility Service** 模拟小爱同学界面操作（需要 Shizuku / Root）
- 效果不稳定，依赖系统更新

**② 用其他唤醒词 App 替代系统助手**
- 安装 Ayega + 第三方语音助手（如 Google Assistant）作为默认
- 让 Google Assistant 接收语音，通过 HTTP webhook → OpenClaw 处理
- 缺点：需要将 Google Assistant 设为默认助手

**③ 最佳实际路径：双助手共存**
- 保留小爱同学（控制米家设备）
- 另外安装 Ayega/Google Assistant 作为 AI 对话入口
- 两套并行，各司其职

---

## 四、Telegram Bot 语音交互方案

### 4.1 Telegram Bot 语音处理原理

```
用户发送语音消息（.ogg）
  → Telegram Bot API 接收
  → 调用语音识别（STT）API
  → 得到文本
  → 发送给 OpenClaw / LLM 处理
  → 将文本/语音回复发回用户
```

### 4.2 现成工具/框架

| 工具 | 特点 | 部署方式 |
|------|------|----------|
| **n8n + Telegram Bot Node** | 工作流自动化，语音消息触发流程 | 自托管 |
| **ChatGPT Telegram Bot** (GitHub 开源) | 接收语音 → STT → GPT → 回复，支持语音/文字双模式 | Docker 部署 |
| **TgBotKit** | Telegram Bot SDK，内置语音处理能力 | Node.js |
| **Python Telegram Bot + Whisper** | 自己写：接收语音 → Whisper API 转文字 → GPT → 回复 | 自部署 |

### 4.3 推荐技术栈（OpenClaw 方向）

OpenClaw 本身已集成 Telegram，如果要让 Telegram Bot 处理语音消息：

```
方案 A（最简）：
Telegram Bot 接收语音消息
  → 转发到 Telegram Bot API 的 getFile 获取音频
  → 调用 OpenAI Whisper API 转文字
  → OpenClaw 处理文字 → 回复

方案 B（更完整）：
用户按住 Telegram 语音按钮说话
  → Bot 接收 → Whisper 转文字
  → OpenClaw/Moran 处理 → TTS 回复或文字回复
```

### 4.4 注意事项

- Telegram 语音消息格式为 `.ogg`（Opus），需要转码后才能用部分 STT 引擎
- Whisper API 支持直接处理 `.ogg` 文件，最简单
- 国内访问 Whisper API 需要代理

---

## 五、综合推荐方案（按 faiz 场景）

### 场景：手机语音 → Moran 回复（替代小爱同学）

#### 🥇 推荐路线：Tasker + OpenClaw Telegram Bot

**架构：**
```
用户对手机说"嘿 Moran，..."
  → Tasker 检测语音（语音触发 Profile）
  → Tasker 调用 HTTP POST 到 OpenClaw
  → OpenClaw 处理并回复
  → Tasker 用系统 TTS 播报回复
```

**实现步骤：**
1. 安装 **MacroDroid** 或 **Tasker**（推荐 MacroDroid，便宜且够用）
2. 配置"语音触发"Profile
3. 配置 HTTP 请求动作，POST 语音内容到 OpenClaw
4. 配置 TTS 动作，播报 OpenClaw 回复

#### 🥈 进阶路线：Ayega 唤醒词 + 自定义语音助手

**架构：**
```
安装 Ayega → 自定义唤醒词（如"墨染"）
  → 触发后录制语音
  → 发送到 OpenClaw Telegram Bot
  → 回复 + TTS 播报
```

#### 🥉 探索路线：完全本地化

```
OpenWakeWord（自定义唤醒词）
  → Rhasspy（本地 ASR + NLU）
  → Ollama（本地 LLM）
  → 本地 TTS
```

---

## 六、风险与注意事项

1. **国内手机品牌助手不开放 API** — 无法直接用小爱/小艺，必须用第三方唤醒词 App 替代或双助手并行
2. **语音识别准确率** — 端侧 STT（如 Whisper.cpp）比云端差，但隐私好、速度快
3. **后台保活** — Android 后台限制严格，Tasker/MacroDroid 需要设置白名单、电池优化
4. **网络延迟** — 全链路（唤醒→识别→LLM→TTS→播报）延迟可能达 3-10 秒，体验不如本地方案
5. **Telegram 在国内访问** — 如果手机在国内，需要考虑 Telegram 的可访问性问题

---

## 七、下一步行动建议

1. **最快路径**：下载 MacroDroid → 配置语音触发 + HTTP → 接入 OpenClaw Webhook（如果 OpenClaw 支持）
2. **验证 Telegram Bot 语音处理**：先测试 Telegram Bot 能否正常接收/处理语音消息
3. **评估延迟接受度**：先跑通全流程，测试响应时间是否可接受
4. **探索 Ayega**：如果想要真正的"语音唤醒"（而不只是手动触发），测试 Ayega 唤醒词效果
