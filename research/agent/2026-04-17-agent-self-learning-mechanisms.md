# Agent 主动学习与反馈捕获机制 - 深度研究报告

**研究主题：** Agent 主动学习与反馈捕获机制
**研究时间：** 2026-04-17
**研究深度：** Standard（多源搜索 + 官方文档）

---

## ⚡ 一句话结论

**OpenClaw 已有 memoryFlush 机制可实现自动化 learnings 写入，SkillClaw evolver 提供了"达到阈值自动升级 skill"的完整闭环设计，比当前"Hook 检测用户反馈 + AI 手动记录"更自动化。**

---

## 📊 置信度：中高

- OpenClaw 机制：基于官方文档，置信度高
- 其他框架：基于社区讨论，置信度中

---

## 🔍 核心发现

### 1. OpenClaw 内置机制

#### memoryFlush（自动化记忆持久化）

```yaml
agents:
  defaults:
    compaction:
      memoryFlush: true  # 开启自动记忆写入
```

- 触发时机：自动压缩前执行 silent agentic turn
- 作用：将当前状态转为持久记忆，无需人工触发

#### SkillClaw Evolver（自动化 Skill 升级）

```
来源：SkillClaw self-improving-agent
模式：达到条件 → 自动更新 SKILL.md
触发条件：
  - 使用频率超过阈值
  - 配置变化频繁
  - 错误率上升到某个水平
```

#### Hook 扩展方向

`agent:session:PostAgentTurn` 可检测：

- 工具调用失败
- 异常长的对话
- 异常路径处理

---

### 2. Claude Code / Claude Agent

**结论：没有公开的 self-improvement 机制文档**

替代方案：

- `session_compact` 手动触发上下文压缩
- compaction safeguard hook 捕获错误摘要
- 系统提示中内置 self-improvement 指令

---

### 3. AutoGPT / LangChain Agents

#### AutoGPT 学习系统

```
- 错误记录（Error Recorder）
- 新任务优先级调整
- Performance Metrics Loop
```

#### LangChain 反射模式

```
代理完成子任务后，主动问自己：
  "我学到了什么新东西？"
  "下次遇到类似情况要注意什么？"
结果存入 memory
```

---

### 4. 其他值得借鉴的设计

#### 阈值触发模式

```
- 定义关键指标（如错误率 > 5%）
- 达到阈值 → 触发 learnings 写入
- 低于阈值 → 不干预
```

#### 定期复盘模式

```
- 每 N 个任务或每 M 小时
- 自动执行"复盘 agentic turn"
- 产出 learnings 报告
```

---

## ❓ 具体问题解答

### Q1: Hook 如何扩展检测 AI 主动发现的问题？

使用 `agent:session:PostAgentTurn` hook + 错误检测逻辑：

```javascript
hook = {
  event: "agent:session:PostAgentTurn",
  condition: (result) => {
    if (result.toolCalls?.some(t => t.error)) return true
    if (result.turns > 10) return true
    return false
  },
  action: "writeLearnings"
}
```

### Q2: 有什么机制让 AI 主动记录？

3 种自动化机制：

| 机制                    | 自动化程度  |
| --------------------- | ------ |
| **memoryFlush**       | ✅ 完全自动 |
| **Threshold Trigger** | ✅ 自动   |
| **Periodic Review**   | ⚠️ 半自动 |

### Q3: 有无自动化 learnings 写入机制？

有，2 个方向：

1. **OpenClaw 原生（memoryFlush）**
   
   ```yaml
   agents.defaults.compaction.memoryFlush: true
   ```

2. **SkillClaw Evolver（更激进）**
   达到条件 → 直接修改 SKILL.md

---

## 💡 可落地建议

### 建议 1：开启 memoryFlush（立即可做）

```yaml
# openclaw.json
agents:
  defaults:
    compaction:
      memoryFlush: true
```

### 建议 2：实现 Threshold Trigger（需开发）

```javascript
{
  threshold: {
    errorRate: 0.05,
    repeatCount: 3,
    toolFailure: 2
  },
  onTrigger: "writeLearnings"
}
```

### 建议 3：采用 SkillClaw Evolver 模式（需开发）

```javascript
{
  counters: { "tool:web_search": 100 },
  triggers: {
    "tool:web_search >= 100": {
      action: "promoteToSKILL",
      target: "web-search-enhanced"
    }
  }
}
```

### 建议 4：系统提示中植入主动记录指令

```
每个任务完成后，主动问自己：
  - 这次学到了什么新东西？
  - 下次遇到类似情况要注意什么？
有价值的发现，记录到 learnings/ 目录
```

---

## 📚 来源

1. **OpenClaw 官方文档** — memoryFlush, compaction, hooks
2. **SkillClaw self-improving-agent** — evolver 模式
   https://github.com/leohuang8688/self-improving-agent
3. **LangChain 反射模式** — Anthropic Claude 反射设计
4. **AutoGPT 内置学习系统** — 错误记录 + Performance Metrics Loop

---

## ⚠️ 局限性

- memoryFlush 需要手动开启，不是默认
- SkillClaw evolver 来自第三方项目，未完全验证
- OpenClaw 最新版本行为可能有变化

---

*研究完成日期：2026-04-17*
*报告路径：/home/morav/.openclaw/workspace/research/agent/2026-04-17-agent-self-learning-mechanisms.md*
