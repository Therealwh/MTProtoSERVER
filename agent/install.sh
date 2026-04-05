#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER — MTG Agent Installer
# Запускается в контейнере с pid:host + network_mode:host
# для прямого доступа к /proc/net/tcp и Docker API
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/mtprotoserver"
AGENT_DIR="/opt/mtg-agent"
AGENT_PORT=9876
AGENT_TOKEN=""

print_sep() { echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

echo ""
print_sep
echo -e "${GREEN}🔧 Установка MTG Agent${NC}"
print_sep
echo ""

mkdir -p "$AGENT_DIR"

# Генерируем токен
AGENT_TOKEN=$(openssl rand -hex 16)
echo -e "${GREEN}Токен агента: ${AGENT_TOKEN}${NC}"

# Создаём docker-compose с pid:host + network_mode:host
cat > "$AGENT_DIR/docker-compose.yml" << EOF
services:
  mtg-agent:
    image: python:3.12-alpine
    container_name: mtg-agent
    restart: unless-stopped
    network_mode: host
    pid: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /proc:/proc:ro
      - ./agent.py:/app/agent.py:ro
    working_dir: /app
    environment:
      - AGENT_TOKEN=${AGENT_TOKEN}
    command: >
      sh -c "pip install -q fastapi uvicorn && python -m uvicorn agent:app --host 0.0.0.0 --port ${AGENT_PORT}"
EOF

# Создаём agent.py — читает /proc/net/tcp напрямую (host network)
cat > "$AGENT_DIR/agent.py" << 'AGENTEOF'
"""
MTG Agent — мониторинг MTProto прокси
Запускается с pid:host + network_mode:host для прямого доступа к /proc/net/tcp
"""
from fastapi import FastAPI, Header, HTTPException
import subprocess
import os
import time
import threading

app = FastAPI(title="MTG Agent")
AGENT_TOKEN = os.environ.get("AGENT_TOKEN", "")
CACHE = {}
CACHE_TIME = 0
CACHE_TTL = 5

def require_token(x_token: str = Header(...)):
    if x_token != AGENT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_proxy_containers():
    try:
        r = subprocess.run(
            ['docker', 'ps', '--filter', 'name=mtproto-proxy', '--format', '{{.Names}}|{{.ID}}|{{.Status}}'],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in r.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    containers.append({'name': parts[0], 'id': parts[1], 'status': parts[2]})
        return containers
    except:
        return []

def get_container_port(name):
    try:
        r = subprocess.run(['docker', 'port', name], capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            return int(r.stdout.strip().split(':')[-1])
    except:
        pass
    return 443

def get_connections_for_port(port):
    """Get active client connections from host /proc/net/tcp"""
    hex_port = format(port, 'X').upper().zfill(4)
    seen_ips = set()
    total = 0
    tg_prefixes = ('149.154.', '95.161.', '91.108.')
    try:
        with open('/proc/net/tcp', 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4 and parts[3] == '01':
                    local = parts[1].split(':')
                    if len(local) >= 2 and local[1].upper() == hex_port:
                        rip_hex = parts[2].split(':')[0]
                        if len(rip_hex) == 8:
                            rip = '.'.join([str(int(rip_hex[i:i+2], 16)) for i in (6,4,2,0)])
                            if rip not in ('127.0.0.1', '0.0.0.0') and not rip.startswith(tg_prefixes):
                                seen_ips.add(rip)
                                total += 1
    except:
        pass
    return {'unique_ips': len(seen_ips), 'connected_ips': sorted(list(seen_ips)), 'total_connections': total}

def get_traffic_for_container(name):
    try:
        r = subprocess.run(['docker', 'inspect', '-f', '{{.State.Pid}}', name],
                          capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            pid = r.stdout.strip()
            dev_file = f'/proc/{pid}/net/dev'
            if os.path.exists(dev_file):
                with open(dev_file, 'r') as f:
                    for line in f:
                        if 'eth0' in line or 'veth' in line:
                            parts = line.strip().split()
                            if len(parts) >= 10:
                                return {'rx_bytes': int(parts[1]), 'tx_bytes': int(parts[9])}
    except:
        pass
    return {'rx_bytes': 0, 'tx_bytes': 0}

def collect_all():
    global CACHE, CACHE_TIME
    containers = get_proxy_containers()
    result = []
    for c in containers:
        port = get_container_port(c['name'])
        connections = get_connections_for_port(port)
        traffic = get_traffic_for_container(c['name'])
        result.append({
            'name': c['name'], 'id': c['id'], 'status': c['status'], 'port': port,
            **connections, **traffic
        })
    CACHE = {'proxies': result}
    CACHE_TIME = time.time()

def background_collector():
    while True:
        try:
            collect_all()
        except:
            pass
        time.sleep(5)

threading.Thread(target=background_collector, daemon=True).start()

@app.get("/health")
async def health():
    return {"status": "ok", "token_set": bool(AGENT_TOKEN)}

@app.get("/proxies")
async def get_proxies(x_token: str = Header(...)):
    require_token(x_token)
    if CACHE and time.time() - CACHE_TIME < CACHE_TTL:
        return CACHE
    collect_all()
    return CACHE

@app.get("/proxies/{name}/connections")
async def get_proxy_connections(name: str, x_token: str = Header(...)):
    require_token(x_token)
    port = get_container_port(name)
    return get_connections_for_port(port)

@app.get("/proxies/{name}/traffic")
async def get_proxy_traffic(name: str, x_token: str = Header(...)):
    require_token(x_token)
    return get_traffic_for_container(name)
AGENTEOF

# Запускаем
cd "$AGENT_DIR"
docker compose up -d
sleep 3

# Проверяем
if curl -s http://localhost:${AGENT_PORT}/health | grep -q "ok"; then
    echo ""
    print_sep
    echo -e "${GREEN}✅ MTG Agent установлен и работает!${NC}"
    print_sep
    echo -e "   Порт: ${AGENT_PORT}"
    echo -e "   Токен: ${AGENT_TOKEN}"
    echo -e "   Health: http://localhost:${AGENT_PORT}/health"
    
    # Сохраняем токен
    mkdir -p "$INSTALL_DIR/config"
    echo "{\"agent_token\": \"${AGENT_TOKEN}\", \"agent_port\": ${AGENT_PORT}}" > "$INSTALL_DIR/config/agent.json"
    echo -e "${GREEN}Токен сохранён в $INSTALL_DIR/config/agent.json${NC}"
else
    echo -e "${RED}❌ Ошибка запуска агента${NC}"
    docker compose logs
    exit 1
fi
