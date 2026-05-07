# TOOLS.md - 工具配置

_所有工具配置的唯一权威。操作规则见 AGENTS.md。_

## MCP Servers

- **serena**：`openclaw mcp set` 已注册，`serena-mcp-server` 命令；`uv tool install` 装在 `~/.local/bin/`
- **notionhq**：本地 `npx @notionhq/notion-mcp-server` 已配置；读写均用 MCP 工具；data_source_id：手写笔记 `0b34f4cf-c8e2-8383-840f-87946b7b821c` / 资源 `b4a4f4cf-c8e2-8348-9f99-07ff23b401bc` / 项目管理器 `3674f4cf-c8e2-8252-ba79-074460dcdc9d`

## Browser

- **VcXsrv**（Windows X Server）：监听 `172.20.112.1:6000`
- **DISPLAY**：`172.20.112.1:0`（固化在 `~/.bashrc`）
- **Chromium 路径**：`/tmp/chrome-extract/opt/google/chrome/chrome`
- **启动脚本**：`~/.openclaw/workspace/scripts/browser-visible.sh`
- **Edge 调试脚本**（Windows）：`C:\Users\morav\scripts\Edge-Remote-Debug.ps1`

## WSL 网络配置

配置入口：`~/.bashrc`（canonical source）

- **代理**：Windows Clash Verge，端口 `127.0.0.1:6984`
- **手动命令**：`proxy_on` / `proxy_off`
- **DISPLAY**：`172.20.112.1:0`
- **Node.js IPv4 优先**：`NODE_OPTIONS="--dns-result-order=ipv4first"`

## OpenClaw 运维

- **exec.host**：`auto`（设为 `gateway` 会被安全策略拦截）
- **沙盒限制**：sub-agent 拒绝访问 workspace 外路径；isolated session 无 exec 权限（`toolsAllow: ["exec"]` 可开启）
- **Browser**：WSL2 下需 `sudo ldconfig` 刷新库缓存
- **沙盒限制详情**：sub-agent 沙盒拒绝访问 workspace 外路径；isolated session 无 exec 权限（`toolsAllow: ["exec"]` 可开启）

## Safe Delete

- **脚本**：`~/.openclaw/workspace/scripts/trash`
- **用法**：`trash <filepath>`
- **回收站**：`~/.trash/`
- **规则**：始终用 trash 代替 rm

## GitHub CLI

- **Token**：保存在 `~/.openclaw/.env`，加载方式：`export $(cat ~/.openclaw/.env | xargs)`
- **账户**：jichangtuijie
- **已验证可用**，新 session 可直接 `export GITHUB_TOKEN` 使用

## ClawHub CLI

- **CLI 路径**：`/home/morav/.local/share/lib/node_modules/clawhub/bin/clawdhub.js`
- **用法**：`node /home/morav/.local/share/lib/node_modules/clawhub/bin/clawdhub.js <命令> --workdir /home/morav/.openclaw/workspace`
- **Skills 安装目录**：`/home/morav/.openclaw/workspace/skills/`
- **仓库**：`jichangtuijie/openclaw-workspace-backup`

## OpenClaw CLI

```
openclaw gateway status/start/stop/restart
openclaw mcp list/set/unset/show
openclaw doctor --non-interactive
```

## 市场研究 Skill

- **market-research（ivan）** → 报告需要数字/百分比时用，侧重真实性、量化数据
- **market-research-agent（1ka）** → 报告需要快速、结构化、有摘要时用，侧重速度和呈现

## 报告集中仓库

- 仓库：jichangtuijie/ai-workforce-report
- GitHub Pages：https://jichangtuijie.github.io/ai-workforce-report/

## Workspace 目录

```
workspace/
├── memory/       — 核心项目记忆与文档
├── research/      — 深度研究报告存档
├── skills/       — 共享技能
├── self-improving/ — 自我改进系统
├── scripts/      — 脚本
├── media/        — 永久媒体（TTS语音、生成的图片/视频）
└── temp/         — 临时文件（处理完清理）
```

---

_工具配置权威。如有安全相关疑问 → AGENTS.md 红线。_
