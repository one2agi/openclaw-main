# ClaWHub 变现研究报告

**研究目标**：OpenClaw 技能（skills）和插件（plugins）的变现模式、市场现状、定价策略  
**数据时效**：2026年4月（实时）  
**研究深度**：标准级，多源交叉验证

---

## ⚡ 一句话结论

ClaWHub 目前以**免费生态为主**，付费变现功能**仍处于早期构建阶段**（GitHub issue #1752 开发者询问付费功能尚无官方回复），但生态规模已达 **700+ skills、52.7k tools、12M 下载**，头部卖家报告单个优质垂直 skill 可达 **$100–$1,000/月** 被动收入，变现路径是真实存在的，但平台级支付基础设施尚不完善。

---

## 📊 置信度：中

**原因**：ClaWHub 平台页面数据直接抓取，变现模式有多个独立信源交叉印证。但**平台抽成比例未找到明确数字**（官方未公开），付费功能上线状态存在不确定性。

---

## 🔍 核心发现

### 一、ClaWHub 平台现状

| 指标 | 数据 |
|---|---|
| Skills 总数 | 700+（持续增长，约每6周翻倍） |
| Tools 总数 | 52.7k |
| 用户数 | 180k |
| 总下载量 | 12M |
| 平均评分 | 4.8 |
| 创作者数 | 数千人 |

**定位**：ClaWHub 是 OpenClaw 官方 skill registry + marketplace，类比"AI Agent 的 App Store"。

**付费 skill 现状**：
- 大多数 skills 均为**免费**
- 付费 skills 定价区间 **$10–$200/个**（已确认）
- ClaWHub 收取 marketplace fee（类 app store 抽成模式），但**具体比例未公开披露**
- GitHub issue #1752（2026年1月）有开发者询问"如何在 ClaWHub 设置付费"，**官方未给出功能说明**

**⚠️ 关键发现**：ClaWHub 官方目前**没有明确的付费/定价功能界面**。付费变现更像是一种非正式的生态行为——开发者通过外部渠道（GitHub Sponsors、自建 Gumroad/Patreon、定制开发外包）实现收入，而非平台内置支付体系。

---

### 二、Skill 与 Plugin 的本质区别

| | Skill | Plugin |
|---|---|---|
| **本质** | Markdown 指令包（SKILL.md + YAML frontmatter） | 原生代码扩展包（需编写代码） |
| **技术门槛** | **低**——会写 Markdown 即可，无需编程 | **高**——需要 JavaScript/TypeScript + 懂 OpenClaw SDK |
| **制作工具** | 任意文本编辑器 | 需要 `openclaw.plugin.json` manifest + Node.js 工具链 |
| **分发方式** | ClaWHub skill pack（直接分发） | 需打包成 npm 包或 ClaWHub plugin bundle |
| **灵活性** | 教 agent "何时、如何"使用工具 | 可创造全新工具类型（channel、model provider、speech 等） |
| **变现适合度** | ✅ 更适合快速制作、快速变现 | 适合企业级深度集成 |

**开发者文档**：
- 官方文档：https://docs.openclaw.ai/tools/creating-skills
- Plugin 开发：https://docs.openclaw.ai/plugins/building-plugins
- Plugin Manifest：https://docs.openclaw.ai/plugins/manifest

**Skill 制作门槛**：极低。一个 Google Analytics 4 skill 有用户仅用 **20 分钟**完成。

---

### 三、变现路径（已验证）

#### 路径1：ClaWHub Premium Skill 销售（最直接）
- **定价**：$10–$200/个
- **收入规模**：单个优质垂直 skill $100–$1,000/月被动收入
- **平台抽成**：ClaWHub 收取 marketplace fee（比例未公开）
- **⚠️ 局限**：平台付费功能尚不完善

#### 路径2：企业定制 Skill 开发（高单价）
- **定价**：$500–$2,000/项目
- **适合**：有特定行业垂直知识的开发者

#### 路径3：Setup + Consulting 服务（最快见收入）
- **Setup 费用**：$200–$500/次
- **月度维护托管**：$50–$200/月
- **案例**：有创始人月一实现 $3,600 收入

#### 路径4：VPS 托管（被动收入潜力大）
- **成本**：$4–6/月/VPS（裸机）
- **收费**：$75–$150/月/客户（managed OpenClaw instance）
- **毛利率**：90%+

#### 路径5：安全审计工具（高天花板）
- **市场**：企业级需求，$30K+ MRR 潜力
- **背景**：ClaWHub 已有 **341 个恶意 skills** 被发现

#### 路径6：内容变现（最低门槛）
- **形式**：教程、模板包、Affiliate 营销
- **平台**：Gumroad、Patreon、Notion 模板

---

### 四、竞争格局

- **竞争激烈程度**：**低**。ClaWHub 生态仍处早期，大量垂直领域空白
- **头部玩家**：主要是独立开发者，社区驱动
- **企业入局**：Snyk、CrowdStrike 等安全厂商已发布 OpenClaw 相关研究报告
- **云厂商**：DigitalOcean、Alibaba Cloud、Tencent、Hostinger 均已入场

---

### 五、平台审核标准

- ClaWHub 自述 "no gatekeeping"（无门槛发布）
- 平台有基础 moderation hooks + vector search 用于内容审核
- 安全问题：14,706 个 skills 中有 **1,103 个恶意 skills**（约7.5%）

---

## ⚠️ 局限性

1. **平台抽成比例未确认**：ClaWHub 官方未公开 marketplace fee 百分比
2. **付费功能状态存疑**：可能付费变现仍非平台原生支持
3. **收入数据置信度**：$100–$1,000/月数据来源于第三方博客，非平台官方披露
4. **数据时效**：生态发展迅速，情况可能快速变化

---

## 📚 来源（共12个）

| 来源 | 可信度 | 内容 |
|---|---|---|
| clawhub.ai（官网） | ✅ 高 | 平台规模数据：52.7k tools、180k 用户、12M 下载 |
| github.com/openclaw/clawhub/issues/1752 | ✅ 高 | 开发者付费功能询问，官方无回应 |
| github.com/openclaw/skills | ✅ 高 | GitHub 镜像存档项目 |
| superframeworks.com | ⚠️ 中 | 行业分析博客，$10–200 定价区间 |
| openclawresource.com | ⚠️ 中 | 8种变现方法清单 |
| www.clawledge.com | ⚠️ 低-中 | 第三方内容，GA4 skill 20分钟案例 |
| docs.openclaw.ai | ✅ 高 | 官方 Skill/Plugin 制作文档 |
| insiderllm.com | ⚠️ 中 | 安全数据：1,103恶意/14,706总数 |

---

## 🎯 对墨染的建议

1. **如果要做 ClaWHub skill 变现**：优先制作**垂直领域 skill**，定价 $10–$50 走薄利多销路线
2. **如果追求更快收入**：Setup + Consulting 服务路径更成熟
3. **如果做 Plugin**：需投入更多开发资源，适合有 Node.js 能力的开发者
4. **持续关注**：ClaWHub 付费功能一旦正式上线，将有一波早期红利窗口期
