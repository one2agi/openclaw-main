# OpenClaw 云服务器安全部署指南

> **适用对象**：将 OpenClaw 部署在云服务器（VPS）上的用户  
> **核心目标**：最小化攻击面，仅允许受控访问，防范 RCE 与暴力破解  
> **适用系统**：Ubuntu 24.04 / Debian 12  
> **修订时间**：2026-04-22

---

## ⚡ 快速结论

- 端口 `18789`（Gateway）**禁止暴露到公网**
- 所有外部访问通过 **Nginx 反向代理 + SSL + 认证 Token**
- 非 root 用户运行，配合防火墙 + fail2ban
- **2026 年 CVE-2026-25253** 敲响警钟：别心存侥幸

---

## 🏗️ 架构总览

```
[外部访问者]
      │
      ▼
[域名解析 → SSL证书 → Nginx 443端口]
      │                        │
      │               反向代理到本地
      ▼                        ▼
[Gateway Loopback 127.0.0.1:18789]
      │
      ▼
[OpenClaw Agent + Skills + Cron]
```

**只有 HTTPS（443）端口对外暴露，Gateway 端口（18789）永远只监听 loopback。**

---

## 📋 完整部署步骤

### 第一阶段：服务器初始化（SSH 后执行）

#### 1.1 创建专用非 root 用户

```bash
# 更新系统
apt update && apt upgrade -y

# 创建专用用户
adduser openclawops
usermod -aG sudo openclawops

# 配置 SSH key（禁止密码登录）
mkdir -p /home/openclawops/.ssh
cp ~/.ssh/authorized_keys /home/openclawops/.ssh/
chmod 700 /home/openclawops/.ssh
chmod 600 /home/openclawops/.ssh/authorized_keys

# 验证后断开 root 连接，用 openclawops 重新登录
```

#### 1.2 防火墙配置（UFW）

```bash
# 设置默认拒绝所有入站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许 SSH（限速，防暴力破解）
sudo ufw allow 22/tcp
sudo ufw limit 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# ⭐ 明确禁止 Gateway 端口暴露
sudo ufw deny 18789/tcp

# 启用防火墙
sudo ufw enable

# 验证规则
sudo ufw status verbose
```

#### 1.3 安装 fail2ban（防暴力破解）

```bash
sudo apt install fail2ban -y

# 创建本地配置（防止包更新覆盖）
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# 编辑 /etc/fail2ban/jail.local 的 [sshd] 部分：
# 确保 enabled = true, maxretry = 5, bantime = 3600

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### 1.4 SSH 加固

编辑 `/etc/ssh/sshd_config`：

```bash
# 不允许密码登录
PasswordAuthentication no

# 只允许 SSH Key
PubkeyAuthentication yes

# 禁止 root 登录
PermitRootLogin no

# 更换默认端口（可选，推荐）
Port 2222

# 重启 SSH
sudo systemctl restart sshd
```

**注意**：换端口后，UFW 规则也要相应更新。

---

### 第二阶段：安装 OpenClaw

#### 2.1 安装 Node.js 24（最低要求 22.16）

```bash
# 添加 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install nodejs -y

# 验证
node --version  # 应输出 v24.x.x
npm --version
```

#### 2.2 全局安装 OpenClaw

```bash
npm install -g openclaw@latest

# 验证安装
openclaw --version
```

#### 2.3 运行引导向导

```bash
openclaw onboard --install-daemon
```

**⭐ 关键：在向导中设置 Gateway Bind 为 `loopback`（不是 `0.0.0.0`）！**

如果错过设置，手动修改：

```bash
openclaw config set gateway.bind loopback
openclaw gateway restart
```

#### 2.4 配置 systemd 服务（开机自启）

```bash
# 开启 lingering（让服务在用户未登录时也能启动）
sudo loginctl enable-linger openclawops

# 启用并启动服务
systemctl --user enable openclaw
systemctl --user start openclaw

# 检查状态
systemctl --user status openclaw

# 查看日志
journalctl --user -u openclaw -f
```

---

### 第三阶段：Nginx 反向代理 + SSL

#### 3.1 安装 Nginx + Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

#### 3.2 创建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/openclaw
```

写入以下内容（替换 `agent.yourdomain.com` 为你的域名）：

```nginx
server {
    listen 80;
    server_name agent.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

**⚠️ `Upgrade` 和 `Connection` 头是必须的，OpenClaw 使用 WebSocket 通信。**

#### 3.3 启用站点 + 获取 SSL

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx

# 获取 SSL 证书（自动配置 HTTPS）
sudo certbot --nginx -d agent.yourdomain.com

# 验证自动续期
sudo certbot renew --dry-run
```

---

### 第四阶段：认证与权限加固

#### 4.1 设置 Gateway 认证 Token

```bash
# 生成强随机 Token
openssl rand -hex 32

# 将其设置为 Gateway token
openclaw config set gateway.token "这里粘贴你的token"
openclaw gateway restart
```

之后每次访问控制台 UI，都需要输入这个 Token。

#### 4.2 锁定凭证目录权限

```bash
# 限制目录访问
chmod 700 ~/.openclaw/credentials/
chmod 600 ~/.openclaw/credentials/*

# 限制主配置目录
chmod 700 ~/.openclaw/
```

**⚠️ OpenClaw 默认将 API Key 明文存储在 `~/.openclaw/credentials/`。这是攻击者的目标，必须锁死。**

---

### 第五阶段：验证与维护

#### 5.1 运行健康检查

```bash
openclaw doctor
```

#### 5.2 测试访问

访问 `https://agent.yourdomain.com`，确认：
- SSL 证书有效
- 需要输入 Gateway Token
- 能正常与 Agent 对话

---

## 🔐 安全检查清单

| 检查项 | 状态 |
|--------|------|
| 非 root 用户运行 OpenClaw | ☐ |
| SSH 使用 Key 登录，禁止密码 | ☐ |
| SSH 端口限速或更换端口 | ☐ |
| UFW 默认拒绝入站，开放 22/80/443 | ☐ |
| Gateway 端口（18789）被 UFW 拒绝 | ☐ |
| Gateway Bind 设置为 loopback | ☐ |
| Nginx 反向代理 + SSL 生效 | ☐ |
| Gateway Token 已设置 | ☐ |
| fail2ban 运行中 | ☐ |
| 凭证目录权限 700 | ☐ |

---

## 🚨 已知漏洞背景

**CVE-2026-25253（2026 年初）**：
- Censys 扫描发现 21,000+ 台暴露的 OpenClaw 实例
- 漏洞成因：Gateway 默认绑定 `0.0.0.0:18789`，导致 WebSocket 劫持 RCE
- **修复方案**：始终使用 `gateway.bind: loopback`，通过 Nginx 代理访问

---

## 📁 关键文件位置

| 路径 | 用途 |
|------|------|
| `~/.openclaw/` | 主配置目录 |
| `~/.openclaw/credentials/` | API Key 存储（需锁死权限） |
| `~/.openclaw/workspace/` | Agent 的 skills、记忆、工作区 |
| `~/.openclaw/openclaw.config.yaml` | 主配置文件 |
| `/etc/nginx/sites-available/openclaw` | Nginx 反向代理配置 |
| `/etc/fail2ban/jail.local` | fail2ban 配置 |

---

## 📌 访问控制方案对比

| 方案 | 适用场景 | 复杂度 |
|------|----------|--------|
| **仅固定 IP 白名单** | 个人使用，IP 固定 | 低 |
| **Cloudflare Access（免费）** | 团队使用，需验证身份 | 中 |
| **VPN（WireGuard）先接入** | 最高安全要求 | 中高 |
| **API Key 验证层** | 公开 Agent 接口 | 高 |

---

## 🆘 紧急处理

### 发现异常访问

```bash
# 查看登录失败日志
sudo lastb

# 查看 fail2ban ban 情况
sudo fail2ban-client status

# 手动封禁 IP
sudo ufw insert 1 deny from <恶意IP>

# 检查 OpenClaw 日志
journalctl --user -u openclaw -n 100
```

### Token 泄露

```bash
# 重新生成 Token
openssl rand -hex 32
openclaw config set gateway.token "新token"
openclaw gateway restart

# 更新所有客户端
```

---

## 📚 参考来源

- RamNode: *Part 2: Installation and Security Hardening | OpenClaw Series*
- LumaDock: *OpenClaw Security Best Practices Guide* (2026-01-29)
- GitHub: knownsec/openclaw-security
- Censys Scanning Data (CVE-2026-25253, 2026)

---

*本指南由墨灵（🔍 faiz 团队深度研究代理）编写。*