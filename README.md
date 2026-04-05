# MTProtoSERVER — MTProto Proxy Control Panel & Management Platform

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Docker](https://img.shields.io/badge/docker-✅-blue)
![FakeTLS](https://img.shields.io/badge/FakeTLS-✅-orange)
![Multi-Node](https://img.shields.io/badge/multi--node-✅-purple)
![2FA](https://img.shields.io/badge/2FA-TOTP-red)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

**Full-featured MTProto proxy management platform with multi-node support, real-time monitoring, and client lifecycle management**

[Quick Install](#-quick-install) • [Features](#-features) • [Architecture](#-architecture) • [API](#-api) • [FAQ](#-faq)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Install](#-quick-install)
- [Step-by-Step Install](#-step-by-step-install)
- [MTG Agent](#-mtg-agent)
- [Web UI](#-web-ui)
- [Telegram Bot](#-telegram-bot)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Uninstall](#-uninstall)

---

## 📖 Overview

**MTProtoSERVER** is a complete platform for deploying and managing MTProto proxy servers with bypass capabilities for Russia and other restricted regions. Built on **mtg v2** — the most modern MTProto engine.

### Key Features:

- 🛡️ **FakeTLS cloaking** — traffic indistinguish from regular HTTPS
- 🇷🇺 **Works in Russia** — bypasses DPI and blocking
- 🖥️ **Multi-node** — manage proxy servers across multiple machines
- 👥 **Client management** — per-client links with limits and auto-stop
- 📊 **Real-time monitoring** — traffic, connections, 24h sparkline charts
- 🌐 **Web UI** — full management dashboard
- 🤖 **Telegram bot** — manage from messenger
- 🔒 **2FA (TOTP)** — Google Authenticator, Aegis, Authy
- 🧦 **SOCKS5** — universal proxy (Dante)
- 🌐 **HTTP/HTTPS** — proxy for browsers (Squid)
- 💰 **Ad-Tag** — monetization via Telegram
- 💾 **Backup/Restore** — from Web UI
- 🌍 **GeoIP** — country blocking
- 🚀 **Speedtest** — from Web UI
- 🔔 **Webhooks** — Discord, Slack notifications
- 🌐 **i18n** — Russian & English
- 🖼️ **Custom logo** — upload your own

---

## ⭐ Features

### 🖥️ Node Management
| Feature | Description |
|---------|-------------|
| **Add/Edit/Delete nodes** | Manage multiple proxy servers |
| **SSH connection** | By password or private key |
| **Country flags** | Visual navigation |
| **Ping & status check** | Test connectivity from UI |
| **Agent sync** | Sync clients from remote nodes |

### 👥 Client Management
| Feature | Description |
|---------|-------------|
| **Auto port & secret** | Automatically assigned on creation |
| **Start/Stop** | Individual client control |
| **QR codes & links** | Quick connection via Telegram |
| **Sync from nodes** | Pull existing clients from remote nodes |
| **Mass view** | See all clients across all nodes |
| **Secret rotation** | Generate new secret, old links die |
| **Traffic reset** | Manual reset per client |

### 📊 Real-time Monitoring
| Feature | Description |
|---------|-------------|
| **RX/TX traffic** | Current period and lifetime |
| **Unique IPs** | Active connections count |
| **24h sparkline** | Connection chart in table |
| **Online cache** | <5ms response from cache |
| **Server resources** | CPU, RAM, Disk usage |

### 🎯 Limits & Automation
| Feature | Description |
|---------|-------------|
| **Traffic limit (GB)** | Auto-stop when exceeded |
| **Device limit** | Auto-stop on unique IP threshold |
| **Expiry date** | Auto-stop after date |
| **Auto-reset traffic** | Daily / Monthly / Yearly schedule |

### 🔒 Security
| Feature | Description |
|---------|-------------|
| **Token auth** | API and UI authentication |
| **TOTP 2FA** | Google Authenticator, Aegis, Authy |
| **IP Blacklist/Whitelist** | Per-IP access control |
| **Firewall management** | Open/close ports from UI |
| **Rate limiting** | Configurable request limits |

### 🌐 Interface
| Feature | Description |
|---------|-------------|
| **Dark/Light theme** | Toggle with persistence |
| **RU/EN languages** | Two languages with toggle |
| **Custom logo** | Upload your own logo |
| **Responsive design** | Works on mobile devices |

### 🧦 SOCKS5 Proxy
| Feature | Description |
|---------|-------------|
| **Dante SOCKS5** | Universal proxy for any app |
| **Multi-user** | Multiple users with different credentials |
| **Authentication** | Login/password per user |

### 🌐 HTTP/HTTPS Proxy
| Feature | Description |
|---------|-------------|
| **Squid** | Most popular HTTP proxy server |
| **Caching** | Speed up via cache |
| **Basic auth** | Username/password authentication |

### 💰 Monetization & Notifications
| Feature | Description |
|---------|-------------|
| **Ad-Tag** | Built-in Telegram ads (@MTProxyBot) |
| **Web UI management** | Set/change Ad-Tag from panel |
| **Webhook alerts** | Discord, Slack, any webhook URL |
| **Webhook test** | Verify from Web UI |

### 🛠️ Diagnostics & Maintenance
| Feature | Description |
|---------|-------------|
| **Speedtest** | Download/upload/ping from Web UI |
| **Health check** | Full system check with one click |
| **Backup/Restore** | Create and restore from Web UI |
| **Logs** | View container logs in real-time |
| **QR codes** | Generate QR for proxy links |
| **Config export** | Download all configs as ZIP |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Panel (Web UI)                     │
│  FastAPI + Jinja2 + Chart.js                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐           │
│  │Dashboard│ │ Clients  │ │ Nodes  │ │ Settings │           │
│  └─────────┘ └──────────┘ └────────┘ └──────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Node 1  │       │ Node 2  │       │ Node N  │
   │ (Local) │       │ Remote  │       │ Remote  │
   │         │       │         │       │         │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │MTG  │ │       │ │MTG  │ │       │ │MTG  │ │
   │ │Proxy│ │       │ │Proxy│ │       │ │Proxy│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │Agent│ │◄──────│ │Agent│ │◄──────│ │Agent│ │
   │ │:9876│ │ HTTP  │ │:9876│ │ HTTP  │ │:9876│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   └─────────┘       └─────────┘       └─────────┘
```

### Components

| Component | Description |
|-----------|-------------|
| **Web UI** | FastAPI dashboard with Jinja2 templates |
| **MTG Proxy** | nineseconds/mtg:2 — MTProto engine with FakeTLS |
| **MTG Agent** | FastAPI HTTP agent on each node for monitoring |
| **Telegram Bot** | python-telegram-bot for remote management |
| **SOCKS5** | Dante — universal SOCKS5 proxy |
| **HTTP Proxy** | Squid — HTTP/HTTPS proxy with caching |

---

## 🚀 Quick Install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

> ⚠️ **Requirements:** Linux (Ubuntu/Debian/CentOS), root access, open port 443

---

## 📖 Step-by-Step Install

### 1. Prepare Server

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Run Installer

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

The installer will guide you through:

1. **System check** — OS detection, dependencies
2. **Docker install** — automatic if not present
3. **MTProto proxies** — how many, ports, domains (1-10 proxies)
4. **Telegram bot** — optional, auto-detects admin Chat ID
5. **SOCKS5 proxy** — optional, with auth
6. **HTTP/HTTPS proxy** — optional, Squid with auth
7. **Ad-Tag** — optional, monetization
8. **GeoIP blocking** — optional, country codes
9. **Webhook notifications** — optional, Discord/Slack
10. **Start** — launches everything

### 3. Access Web UI

After installation, open: `http://YOUR_IP:8080`

### 4. Install MTG Agent on Remote Nodes

On each remote server:

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/agent/install.sh | bash -s -- --port 9876 --token YOUR_SECRET_TOKEN
```

Then add the node in the Web UI → Nodes page.

---

## 🤖 MTG Agent

The MTG Agent is a lightweight FastAPI HTTP service installed on each proxy node. It provides:

- **Real-time client data** — traffic, unique IPs, status
- **24h connection history** — sparkline charts
- **Client lifecycle** — create, start, stop, restart, delete
- **System monitoring** — CPU, RAM, disk
- **Caching** — <5ms responses from 30s cache

### Agent API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/clients` | GET | List all MTG clients with stats |
| `/clients/{label}/history` | GET | 24h connection history |
| `/clients/{label}/start` | POST | Start a client |
| `/clients/{label}/stop` | POST | Stop a client |
| `/clients/{label}/restart` | POST | Restart a client |
| `/clients/create` | POST | Create new MTG client |
| `/clients/{label}` | DELETE | Delete a client |
| `/system` | GET | System resources |

All endpoints require `x-token` header.

---

## 🎛️ Web UI

### Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Overview, Docker containers, resources, quick actions |
| **Clients** | Add/manage clients with limits, QR codes, sparklines |
| **Nodes** | Add/manage nodes, ping test, sync, agent install |
| **Statistics** | Traffic charts, client details, system resources |
| **SOCKS5** | SOCKS5 proxy info and user management |
| **HTTP/HTTPS** | HTTP proxy info and usage instructions |
| **Logs** | Container logs in real-time |
| **Backup** | Create, restore, delete backups |
| **Security** | IP blacklist/whitelist, firewall, rate limiting, export |
| **Settings** | Auth token, 2FA, logo, Ad-Tag, domain rotation, webhook, speedtest |

---

## 🤖 Telegram Bot

Commands available through inline menu:

| Command | Description |
|---------|-------------|
| `/start` | Main menu with inline buttons |
| 📊 Status | Proxy info and stats |
| 🌐 Proxies | List all proxy servers |
| 👥 Users | List and manage users |
| ➕ Add User | Create new user with proxy selection |
| 📈 Statistics | Overall traffic stats |
| 🔧 Diagnostics | System health check |

---

## 📡 API Reference

### Authentication

```bash
curl -H "x-token: YOUR_TOKEN" https://your-server/api/status
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/clients/add` | POST | Add new client |
| `/api/clients/{id}/toggle` | POST | Enable/disable client |
| `/api/clients/{id}/delete` | POST | Delete client |
| `/api/clients/{id}/rotate` | POST | Rotate client secret |
| `/api/clients/{id}/reset-traffic` | POST | Reset traffic counters |
| `/api/nodes/add` | POST | Add new node |
| `/api/nodes/{id}/ping` | POST | Ping node |
| `/api/nodes/{id}/sync` | POST | Sync clients from node |
| `/api/system/backup` | POST | Create backup |
| `/api/system/restore` | POST | Restore from backup |
| `/api/system/health` | GET | Health check |
| `/api/system/speedtest` | GET | Speed test |
| `/api/qr?text=...` | GET | Generate QR code |
| `/api/metrics` | GET | Prometheus metrics |

---

## 🛡️ Security

### Recommendations

1. **Enable 2FA** — Settings → Two-Factor Authentication
2. **Change default token** — Settings → Authentication
3. **Use strong agent tokens** — Different token per node
4. **Open only required ports** — 443 for proxy, 8080 for Web UI
5. **Enable GeoIP blocking** — Block unwanted countries
6. **Regular backups** — Use the Backup page

### Firewall (UFW)

```bash
sudo ufw allow 443/tcp    # MTProto proxy
sudo ufw allow 8080/tcp   # Web UI (restrict by IP)
sudo ufw allow 1080/tcp   # SOCKS5 (if enabled)
sudo ufw allow 3128/tcp   # HTTP proxy (if enabled)
sudo ufw enable
```

---

## 🔧 Troubleshooting

### Proxy not connecting

1. Check containers: `docker compose ps`
2. Check port 443: `ss -tlnp | grep 443`
3. Check firewall: `sudo ufw status`
4. Check logs: `docker compose logs mtproto-proxy`

### Web UI not loading

1. Check container: `docker compose ps mtproto-webui`
2. Check port: `ss -tlnp | grep 8080`
3. Open port: `sudo ufw allow 8080/tcp`

### Agent not responding

1. Check agent: `curl http://NODE_IP:9876/health`
2. Check token: Ensure token matches in both panel and agent
3. Restart agent: `cd /opt/mtg-agent && docker compose restart`

### Health Check

```bash
curl http://YOUR_IP:8080/api/system/health
```

---

## ❓ FAQ

### Q: How many clients can I create?
A: Limited by server resources. On a minimal VPS (1 core, 512MB RAM) — up to 100 clients.

### Q: How do I add a client?
A: Web UI → Clients → Add Client form, or via API `/api/clients/add`.

### Q: How do I add a remote node?
A: Install the agent on the remote server, then add it in Web UI → Nodes.

### Q: How do I change the masking domain?
A: Settings → Domain Rotation, or run `bash /opt/mtprotoserver/scripts/rotate-domain.sh`.

### Q: How do I update?
A: `cd /opt/mtprotoserver && docker compose pull && docker compose up -d`

### Q: Is this legal?
A: MTProto is Telegram's official proxy protocol. Using proxies to access legal resources is not prohibited.

---

## 🗑️ Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/uninstall.sh | sudo bash -s -- -y
```

Or manually:
```bash
cd /opt/mtprotoserver
docker compose down
cd ..
sudo rm -rf /opt/mtprotoserver
```

---

## 📁 Project Structure

```
MTProtoSERVER/
├── install.sh                    # Main installer (interactive)
├── uninstall.sh                  # Uninstaller
├── README.md                     # Documentation
├── .gitignore
│
├── agent/                        # MTG Agent for remote nodes
│   ├── Dockerfile
│   ├── agent.py                  # FastAPI agent for monitoring
│   ├── requirements.txt
│   └── install.sh                # One-click agent installer
│
├── webui/                        # Web Control Panel
│   ├── Dockerfile
│   ├── app.py                    # FastAPI application
│   ├── requirements.txt
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html             # Base layout with sidebar
│   │   ├── dashboard.html        # Main dashboard
│   │   ├── clients.html          # Client management
│   │   ├── nodes.html            # Node management
│   │   ├── stats.html            # Statistics & charts
│   │   ├── settings.html         # Settings & 2FA
│   │   ├── security.html         # Security & firewall
│   │   ├── logs.html             # Container logs
│   │   ├── backup.html           # Backup & restore
│   │   ├── socks5.html           # SOCKS5 management
│   │   └── http_proxy.html       # HTTP proxy info
│   └── static/
│       ├── css/style.css         # Styles (dark/light theme)
│       └── js/app.js             # JavaScript (i18n, theme)
│
├── bot/                          # Telegram Bot
│   ├── Dockerfile
│   ├── bot.py                    # Telegram bot
│   └── requirements.txt
│
├── scripts/                      # Helper scripts
│   ├── auto-heal.sh              # Auto-restart on failure
│   ├── auto-update.sh            # Auto-update images
│   ├── backup.sh                 # Config backup
│   ├── monitor.sh                # Availability monitoring
│   ├── rotate-domain.sh          # Domain rotation
│   ├── health-check.sh           # System diagnostics
│   ├── speedtest.sh              # Speed test
│   ├── add-proxy.sh              # Add proxy interactively
│   └── remove-proxy.sh           # Remove proxy by label
│
└── config/                       # Configuration files
    ├── domains.txt               # FakeTLS domain list
    └── geoblock.txt              # GeoIP blocklist
```

---

## 📄 License

MIT License — free to use with attribution.

---

<div align="center">

**MTProtoSERVER v2.0.0** | 2026

Made with ❤️ for free access to Telegram

</div>
