"""
MTG Agent — FastAPI HTTP агент для мониторинга и управления MTG контейнерами
Устанавливается на каждую ноду. Считает уникальные IP, трафик, подключения.
"""
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import docker
import psutil
import time
import os
import json
import threading
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(title="MTG Agent")

API_TOKEN = os.environ.get("AGENT_TOKEN", "changeme")
CACHE = {}
CACHE_TTL = 5  # seconds
TRAFFIC_HISTORY = {}  # {client_label: [{timestamp, rx, tx, connections}]}

def require_token(x_token: str = Header(...)):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docker not available: {e}")

def is_mtg_container(c):
    return 'mtg' in c.image.tags[0].lower() if c.image.tags else False

def get_container_label(c):
    return c.labels.get('mtg_client_label', c.name.replace('mtg-', ''))

def get_container_port(c):
    ports = c.attrs.get('NetworkSettings', {}).get('Ports', {})
    for p in ports:
        if ports[p]:
            return int(ports[p][0].get('HostPort', p.split('/')[0]))
    return 0

def get_container_secret(c):
    cmd = c.attrs.get('Config', {}).get('Cmd', [])
    for i, arg in enumerate(cmd):
        if arg.startswith('ee') or arg.startswith('dd') or arg.startswith('tls-'):
            return arg
        if arg.startswith('secret='):
            return arg.split('=', 1)[1]
    return ''

def get_unique_ips(c):
    try:
        result = c.exec_run('ss -tn state established', demux=True)
        if result[0] == 0:
            lines = result[1].decode().strip().split('\n')[1:]
            ips = set()
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    remote = parts[4].rsplit(':', 1)[0]
                    if remote and remote != '127.0.0.1':
                        ips.add(remote)
            return len(ips)
    except:
        pass
    return 0

def get_traffic_stats(c):
    stats = c.stats(stream=False)
    net = stats.get('networks', {})
    rx = sum(n.get('rx_bytes', 0) for n in net.values())
    tx = sum(n.get('tx_bytes', 0) for n in net.values())
    return rx, tx

def collect_all():
    """Собирает данные со всех MTG контейнеров"""
    try:
        client = get_docker_client()
        containers = client.containers.list(all=True)
        results = []
        for c in containers:
            if not is_mtg_container(c):
                continue
            label = get_container_label(c)
            port = get_container_port(c)
            secret = get_container_secret(c)
            status = c.status
            unique_ips = get_unique_ips(c) if status == 'running' else 0
            rx, tx = get_traffic_stats(c) if status == 'running' else (0, 0)

            # Сохраняем историю
            now = datetime.now().isoformat()
            if label not in TRAFFIC_HISTORY:
                TRAFFIC_HISTORY[label] = []
            TRAFFIC_HISTORY[label].append({
                'timestamp': now,
                'rx': rx,
                'tx': tx,
                'connections': unique_ips
            })
            # Храним последние 288 записей (24 часа при сборе каждые 5 мин)
            TRAFFIC_HISTORY[label] = TRAFFIC_HISTORY[label][-288:]

            results.append({
                'label': label,
                'name': c.name,
                'port': port,
                'secret': secret,
                'status': status,
                'unique_ips': unique_ips,
                'rx_bytes': rx,
                'tx_bytes': tx,
                'image': c.image.tags[0] if c.image.tags else '',
                'created': c.attrs.get('Created', ''),
            })

        CACHE['data'] = results
        CACHE['timestamp'] = time.time()
        CACHE['system'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 1),
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 1),
            'disk_percent': psutil.disk_usage('/').percent,
            'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 1),
            'disk_used_gb': round(psutil.disk_usage('/').used / (1024**3), 1),
        }
        return results
    except Exception as e:
        return {'error': str(e)}

# Фоновый сборщик
def background_collector():
    while True:
        try:
            collect_all()
        except:
            pass
        time.sleep(30)

threading.Thread(target=background_collector, daemon=True).start()

# =================== API ===================

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "token_set": bool(API_TOKEN != "changeme")}

@app.get("/clients")
async def get_clients(x_token: str = Header(...)):
    require_token(x_token)
    # Возвращаем из кэша если свежий
    if 'data' in CACHE and time.time() - CACHE.get('timestamp', 0) < CACHE_TTL:
        return {"clients": CACHE['data'], "system": CACHE.get('system', {})}
    data = collect_all()
    return {"clients": CACHE.get('data', []), "system": CACHE.get('system', {})}

@app.get("/clients/{label}/history")
async def get_client_history(label: str, x_token: str = Header(...)):
    require_token(x_token)
    history = TRAFFIC_HISTORY.get(label, [])
    return {"label": label, "history": history}

@app.post("/clients/{label}/start")
async def start_client(label: str, x_token: str = Header(...)):
    require_token(x_token)
    client = get_docker_client()
    try:
        c = client.containers.get(f'mtg-{label}')
        c.start()
        return {"status": "ok", "action": "started"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Client not found")

@app.post("/clients/{label}/stop")
async def stop_client(label: str, x_token: str = Header(...)):
    require_token(x_token)
    client = get_docker_client()
    try:
        c = client.containers.get(f'mtg-{label}')
        c.stop()
        return {"status": "ok", "action": "stopped"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Client not found")

@app.post("/clients/{label}/restart")
async def restart_client(label: str, x_token: str = Header(...)):
    require_token(x_token)
    client = get_docker_client()
    try:
        c = client.containers.get(f'mtg-{label}')
        c.restart()
        return {"status": "ok", "action": "restarted"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Client not found")

@app.post("/clients/create")
async def create_client(data: dict, x_token: str = Header(...)):
    require_token(x_token)
    client = get_docker_client()
    label = data.get('label', 'client')
    port = data.get('port', 0)
    secret = data.get('secret', '')
    domain = data.get('domain', 'cloudflare.com')

    if not secret:
        import secrets
        domain_hex = domain.encode().hex()
        secret = f"ee{secrets.token_hex(14)}{domain_hex}"

    if not port:
        # Найти свободный порт начиная с 443
        port = 443
        while True:
            try:
                result = client.containers.run(
                    'alpine', f'ss -tlnp sport = :{port}', remove=True,
                    stdout=True, stderr=True
                )
                if b'LISTEN' not in result:
                    break
            except:
                break
            port += 1

    container = client.containers.run(
        'nineseconds/mtg:2',
        name=f'mtg-{label}',
        command=['simple-run', '-n', '1.1.1.1', '-i', 'prefer-ipv4', f'0.0.0.0:{port}', secret],
        ports={f'{port}/tcp': port},
        restart_policy={'Name': 'unless-stopped'},
        labels={'mtg_client_label': label},
        detach=True
    )

    return {
        "status": "ok",
        "label": label,
        "port": port,
        "secret": secret,
        "link": f"tg://proxy?server={data.get('server_ip', '')}&port={port}&secret={secret}"
    }

@app.delete("/clients/{label}")
async def delete_client(label: str, x_token: str = Header(...)):
    require_token(x_token)
    client = get_docker_client()
    try:
        c = client.containers.get(f'mtg-{label}')
        c.remove(force=True)
        if label in TRAFFIC_HISTORY:
            del TRAFFIC_HISTORY[label]
        return {"status": "ok", "action": "deleted"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Client not found")

@app.get("/system")
async def get_system(x_token: str = Header(...)):
    require_token(x_token)
    if 'system' in CACHE:
        return CACHE['system']
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 1),
        'disk_percent': psutil.disk_usage('/').percent,
        'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 1),
        'disk_used_gb': round(psutil.disk_usage('/').used / (1024**3), 1),
    }
