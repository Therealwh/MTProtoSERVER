from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import subprocess
import secrets as sec
import psutil
import io
import qrcode
import time
import base64
import hashlib
import struct
import hmac
import re
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(title="MTProtoSERVER Control Panel")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DATA_DIR = "/app/data"
CONFIG_DIR = "/app/config"
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
NODES_FILE = os.path.join(DATA_DIR, "nodes.json")
LOGO_FILE = os.path.join(DATA_DIR, "logo.png")

# =================== AUTH ===================

def load_auth():
    try:
        with open(os.path.join(CONFIG_DIR, "auth.json")) as f:
            return json.load(f)
    except:
        return {"token": "", "totp_secret": "", "totp_enabled": False}

def save_auth(data):
    with open(os.path.join(CONFIG_DIR, "auth.json"), 'w') as f:
        json.dump(data, f, indent=4)

def generate_totp_secret():
    return base64.b32encode(sec.token_bytes(20)).decode()

def verify_totp(secret, token, window=1):
    if not secret or not token or len(token) != 6:
        return False
    try:
        key = base64.b32decode(secret)
        token_int = int(token)
        for i in range(-window, window + 1):
            epoch = int(time.time()) // 30 + i
            msg = struct.pack('>Q', epoch)
            h = hmac.new(key, msg, hashlib.sha1).digest()
            o = h[19] & 15
            h_int = struct.unpack('>I', h[o:o+4])[0] & 0x7fffffff
            if h_int % 1000000 == token_int:
                return True
    except:
        pass
    return False

def get_totp_uri(secret, username="MTProtoSERVER"):
    return f"otpauth://totp/{username}?secret={secret}&issuer=MTProtoSERVER"

# =================== DATA HELPERS ===================

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_settings():
    return load_json(SETTINGS_FILE)

def save_settings(data):
    save_json(SETTINGS_FILE, data)

def get_clients():
    return load_json(CLIENTS_FILE)

def save_clients(data):
    save_json(CLIENTS_FILE, data)

def get_nodes():
    return load_json(NODES_FILE)

def save_nodes(data):
    save_json(NODES_FILE, data)

def get_proxy_link(ip, port, secret):
    return f"tg://proxy?server={ip}&port={port}&secret={secret}"

def run_docker_cmd(args, timeout=30):
    try:
        result = subprocess.run(
            ['docker', 'compose'] + args,
            capture_output=True, text=True, cwd='/opt/mtprotoserver',
            timeout=timeout
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return str(e)

def get_docker_status():
    containers = []
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}|{{.Status}}|{{.Ports}}'],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 3:
                    containers.append({'name': parts[0], 'status': parts[1], 'ports': parts[2]})
    except:
        pass
    return containers

def get_system_info():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': mem.percent,
        'memory_total_gb': round(mem.total / (1024**3), 1),
        'memory_used_gb': round(mem.used / (1024**3), 1),
        'disk_percent': disk.percent,
        'disk_total_gb': round(disk.total / (1024**3), 1),
        'disk_used_gb': round(disk.used / (1024**3), 1),
    }

def format_bytes(b):
    if b == 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

# =================== I18N ===================

LANG = {
    'ru': {
        'dashboard': 'Дашборд', 'clients': 'Клиенты', 'nodes': 'Ноды',
        'stats': 'Статистика', 'settings': 'Настройки', 'security': 'Безопасность',
        'logs': 'Логи', 'backup': 'Бэкап', 'socks5': 'SOCKS5', 'http_proxy': 'HTTP/HTTPS',
    },
    'en': {
        'dashboard': 'Dashboard', 'clients': 'Clients', 'nodes': 'Nodes',
        'stats': 'Statistics', 'settings': 'Settings', 'security': 'Security',
        'logs': 'Logs', 'backup': 'Backup', 'socks5': 'SOCKS5', 'http_proxy': 'HTTP/HTTPS',
    }
}

def get_lang(request: Request):
    return request.query_params.get('lang', 'ru')

# =================== PAGES ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    clients_data = get_clients()
    nodes_data = get_nodes()
    system = get_system_info()
    containers = get_docker_status()
    clients = clients_data.get('clients', [])
    nodes = nodes_data.get('nodes', [])
    active_clients = len([c for c in clients if c.get('enabled', True)])
    total_rx = sum(c.get('rx_bytes', 0) for c in clients)
    total_tx = sum(c.get('tx_bytes', 0) for c in clients)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "settings": settings,
        "clients": clients,
        "nodes": nodes,
        "clients_count": len(clients),
        "active_clients": active_clients,
        "nodes_count": len(nodes),
        "total_rx": format_bytes(total_rx),
        "total_tx": format_bytes(total_tx),
        "system": system,
        "containers": containers,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    clients_data = get_clients()
    nodes_data = get_nodes()
    settings = get_settings()
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients_data.get('clients', []),
        "nodes": nodes_data.get('nodes', []),
        "settings": settings,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/nodes", response_class=HTMLResponse)
async def nodes_page(request: Request):
    nodes_data = get_nodes()
    return templates.TemplateResponse("nodes.html", {
        "request": request,
        "nodes": nodes_data.get('nodes', []),
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    clients_data = get_clients()
    system = get_system_info()
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "clients": clients_data.get('clients', []),
        "system": system,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = get_settings()
    auth = load_auth()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "auth": auth,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("security.html", {
        "request": request,
        "settings": settings,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request):
    return templates.TemplateResponse("backup.html", {
        "request": request,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/socks5", response_class=HTMLResponse)
async def socks5_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("socks5.html", {
        "request": request,
        "settings": settings,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

@app.get("/http-proxy", response_class=HTMLResponse)
async def http_proxy_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("http_proxy.html", {
        "request": request,
        "settings": settings,
        "lang": get_lang(request),
        "has_logo": os.path.exists(LOGO_FILE)
    })

# =================== AUTH API ===================

@app.post("/api/auth/login")
async def login(request: Request):
    form = await request.form()
    token = form.get('token', '')
    totp = form.get('totp', '')
    auth = load_auth()

    if not auth.get('token'):
        # First login — set token
        if not token:
            return JSONResponse({'status': 'error', 'message': 'Token required'}, status_code=400)
        auth['token'] = token
        save_auth(auth)
        return JSONResponse({'status': 'ok', 'first_setup': True})

    if token != auth['token']:
        return JSONResponse({'status': 'error', 'message': 'Invalid token'}, status_code=401)

    if auth.get('totp_enabled') and auth.get('totp_secret'):
        if not verify_totp(auth['totp_secret'], totp):
            return JSONResponse({'status': 'error', 'message': 'Invalid TOTP', 'totp_required': True}, status_code=401)

    return JSONResponse({'status': 'ok'})

@app.get("/api/auth/totp-setup")
async def totp_setup():
    auth = load_auth()
    if not auth.get('totp_secret'):
        auth['totp_secret'] = generate_totp_secret()
        save_auth(auth)
    return JSONResponse({
        'secret': auth['totp_secret'],
        'uri': get_totp_uri(auth['totp_secret'])
    })

@app.post("/api/auth/totp-enable")
async def totp_enable(request: Request):
    form = await request.form()
    code = form.get('code', '')
    auth = load_auth()
    if verify_totp(auth.get('totp_secret', ''), code):
        auth['totp_enabled'] = True
        save_auth(auth)
        return JSONResponse({'status': 'ok'})
    return JSONResponse({'status': 'error', 'message': 'Invalid code'}, status_code=400)

@app.post("/api/auth/totp-disable")
async def totp_disable():
    auth = load_auth()
    auth['totp_enabled'] = False
    save_auth(auth)
    return JSONResponse({'status': 'ok'})

@app.post("/api/auth/change-token")
async def change_token(request: Request):
    form = await request.form()
    new_token = form.get('token', '')
    if not new_token:
        return JSONResponse({'status': 'error', 'message': 'Token required'}, status_code=400)
    auth = load_auth()
    auth['token'] = new_token
    save_auth(auth)
    return JSONResponse({'status': 'ok'})

# =================== CLIENTS API ===================

@app.post("/api/clients/add")
async def add_client(request: Request):
    form = await request.form()
    label = form.get('label', 'client')
    node_id = int(form.get('node_id', 0))
    traffic_limit_gb = float(form.get('traffic_limit_gb', 0))
    device_limit = int(form.get('device_limit', 0))
    expiry_days = int(form.get('expiry_days', 0))

    settings = get_settings()
    clients_data = get_clients()
    clients = clients_data.get('clients', [])
    next_id = clients_data.get('next_id', 1)

    domain = form.get('domain', settings.get('fake_domain', 'cloudflare.com'))
    domain_hex = domain.encode().hex()
    secret = f"ee{sec.token_hex(14)}{domain_hex}"

    # Auto port
    port = 443 + next_id

    expiry_date = ''
    if expiry_days > 0:
        expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d')

    new_client = {
        'id': next_id,
        'label': label,
        'node_id': node_id,
        'port': port,
        'domain': domain,
        'secret': secret,
        'enabled': True,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'traffic_limit_gb': traffic_limit_gb,
        'device_limit': device_limit,
        'expiry_date': expiry_date,
        'auto_reset': form.get('auto_reset', 'never'),
        'rx_bytes': 0,
        'tx_bytes': 0,
        'unique_ips': 0,
        'connections': 0,
        'history': []
    }

    clients.append(new_client)
    clients_data['clients'] = clients
    clients_data['next_id'] = next_id + 1
    save_clients(clients_data)

    link = get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), port, secret)
    return JSONResponse({'status': 'ok', 'secret': secret, 'link': link, 'port': port})

@app.post("/api/clients/{client_id}/toggle")
async def toggle_client(client_id: int):
    clients_data = get_clients()
    for c in clients_data.get('clients', []):
        if c['id'] == client_id:
            c['enabled'] = not c.get('enabled', True)
            break
    save_clients(clients_data)
    return JSONResponse({'status': 'ok', 'enabled': c['enabled']})

@app.post("/api/clients/{client_id}/delete")
async def delete_client(client_id: int):
    clients_data = get_clients()
    clients_data['clients'] = [c for c in clients_data.get('clients', []) if c['id'] != client_id]
    save_clients(clients_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/clients/{client_id}/rotate")
async def rotate_client(client_id: int):
    clients_data = get_clients()
    settings = get_settings()
    for c in clients_data.get('clients', []):
        if c['id'] == client_id:
            domain_hex = c.get('domain', 'cloudflare.com').encode().hex()
            c['secret'] = f"ee{sec.token_hex(14)}{domain_hex}"
            break
    save_clients(clients_data)
    link = get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), c['port'], c['secret'])
    return JSONResponse({'status': 'ok', 'secret': c['secret'], 'link': link})

@app.post("/api/clients/{client_id}/reset-traffic")
async def reset_traffic(client_id: int):
    clients_data = get_clients()
    for c in clients_data.get('clients', []):
        if c['id'] == client_id:
            c['rx_bytes'] = 0
            c['tx_bytes'] = 0
            break
    save_clients(clients_data)
    return JSONResponse({'status': 'ok'})

@app.get("/api/clients/{client_id}/history")
async def get_client_history(client_id: int):
    clients_data = get_clients()
    for c in clients_data.get('clients', []):
        if c['id'] == client_id:
            return JSONResponse({'history': c.get('history', [])})
    return JSONResponse({'history': []})

# =================== NODES API ===================

@app.post("/api/nodes/add")
async def add_node(request: Request):
    form = await request.form()
    nodes_data = get_nodes()
    nodes = nodes_data.get('nodes', [])
    next_id = nodes_data.get('next_id', 1)

    new_node = {
        'id': next_id,
        'name': form.get('name', 'node'),
        'ip': form.get('ip', ''),
        'port': int(form.get('port', 9876)),
        'country': form.get('country', '🌍'),
        'token': form.get('token', ''),
        'auth_type': form.get('auth_type', 'token'),
        'ssh_user': form.get('ssh_user', ''),
        'ssh_pass': form.get('ssh_pass', ''),
        'ssh_key': form.get('ssh_key', ''),
        'enabled': True,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_ping': '',
        'status': 'unknown'
    }

    nodes.append(new_node)
    nodes_data['nodes'] = nodes
    nodes_data['next_id'] = next_id + 1
    save_nodes(nodes_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{node_id}/toggle")
async def toggle_node(node_id: int):
    nodes_data = get_nodes()
    for n in nodes_data.get('nodes', []):
        if n['id'] == node_id:
            n['enabled'] = not n.get('enabled', True)
            break
    save_nodes(nodes_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{node_id}/delete")
async def delete_node(node_id: int):
    nodes_data = get_nodes()
    nodes_data['nodes'] = [n for n in nodes_data.get('nodes', []) if n['id'] != node_id]
    save_nodes(nodes_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{node_id}/ping")
async def ping_node(node_id: int):
    nodes_data = get_nodes()
    for n in nodes_data.get('nodes', []):
        if n['id'] == node_id:
            try:
                import requests as req
                url = f"http://{n['ip']}:{n['port']}/health"
                r = req.get(url, timeout=5)
                n['status'] = 'online' if r.status_code == 200 else 'offline'
                n['last_ping'] = datetime.now().strftime('%H:%M:%S')
                save_nodes(nodes_data)
                return JSONResponse({'status': 'ok', 'node_status': n['status'], 'last_ping': n['last_ping']})
            except:
                n['status'] = 'offline'
                n['last_ping'] = datetime.now().strftime('%H:%M:%S')
                save_nodes(nodes_data)
                return JSONResponse({'status': 'ok', 'node_status': 'offline', 'last_ping': n['last_ping']})
    return JSONResponse({'status': 'error', 'message': 'Node not found'}, status_code=404)

@app.post("/api/nodes/{node_id}/sync")
async def sync_node(node_id: int):
    nodes_data = get_nodes()
    clients_data = get_clients()
    for n in nodes_data.get('nodes', []):
        if n['id'] == node_id:
            try:
                import requests as req
                url = f"http://{n['ip']}:{n['port']}/clients"
                headers = {'x-token': n['token']}
                r = req.get(url, headers=headers, timeout=10)
                remote_clients = r.json().get('clients', [])
                # Merge with local
                local_clients = clients_data.get('clients', [])
                for rc in remote_clients:
                    found = False
                    for lc in local_clients:
                        if lc['label'] == rc['label']:
                            lc['rx_bytes'] = rc.get('rx_bytes', 0)
                            lc['tx_bytes'] = rc.get('tx_bytes', 0)
                            lc['unique_ips'] = rc.get('unique_ips', 0)
                            lc['status'] = rc.get('status', 'unknown')
                            found = True
                            break
                    if not found:
                        local_clients.append(rc)
                clients_data['clients'] = local_clients
                save_clients(clients_data)
                return JSONResponse({'status': 'ok', 'synced': len(remote_clients)})
            except Exception as e:
                return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)
    return JSONResponse({'status': 'error', 'message': 'Node not found'}, status_code=404)

# =================== SYSTEM API ===================

@app.post("/api/system/restart")
async def restart_system():
    msg = run_docker_cmd(['restart'])
    return JSONResponse({'status': 'ok', 'message': msg})

@app.post("/api/system/restart-container")
async def restart_container(request: Request):
    form = await request.form()
    name = form.get('name', '')
    if name:
        msg = run_docker_cmd(['restart', name])
        return JSONResponse({'status': 'ok', 'message': msg})
    return JSONResponse({'status': 'error', 'message': 'No name'}, status_code=400)

@app.get("/api/system/logs")
async def get_logs(lines: int = 100):
    logs = run_docker_cmd(['logs', '--tail', str(lines)])
    return JSONResponse({'status': 'ok', 'logs': logs})

@app.post("/api/system/backup")
async def create_backup():
    import datetime
    backup_dir = '/opt/mtprotoserver/backups'
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{timestamp}.tar.gz'
    filepath = os.path.join(backup_dir, filename)
    try:
        subprocess.run(['tar', '-czf', filepath, '-C', '/opt/mtprotoserver',
                        'config', 'data', 'docker-compose.yml'],
                       capture_output=True, timeout=30)
        size = os.path.getsize(filepath)
        size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
        return JSONResponse({'status': 'ok', 'filename': filename, 'size': size_str})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.get("/api/system/backups")
async def list_backups():
    backup_dir = '/opt/mtprotoserver/backups'
    backups = []
    if os.path.exists(backup_dir):
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.tar.gz'):
                size = os.path.getsize(os.path.join(backup_dir, f))
                size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
                backups.append({'name': f, 'size': size_str})
    return JSONResponse({'backups': backups})

@app.post("/api/system/restore")
async def restore_backup(request: Request):
    form = await request.form()
    name = form.get('name', '')
    filepath = os.path.join('/opt/mtprotoserver/backups', name)
    if not os.path.exists(filepath):
        return JSONResponse({'status': 'error', 'message': 'Backup not found'}, status_code=404)
    try:
        subprocess.run(['tar', '-xzf', filepath, '-C', '/opt/mtprotoserver'],
                       capture_output=True, timeout=30)
        return JSONResponse({'status': 'ok'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/delete-backup")
async def delete_backup(request: Request):
    form = await request.form()
    name = form.get('name', '')
    filepath = os.path.join('/opt/mtprotoserver/backups', name)
    if os.path.exists(filepath):
        os.remove(filepath)
    return JSONResponse({'status': 'ok'})

@app.get("/api/system/health")
async def health_check():
    checks = []
    try:
        r = subprocess.run(['docker', 'info'], capture_output=True, timeout=5)
        checks.append(f"{'✅' if r.returncode == 0 else '❌'} Docker: {'работает' if r.returncode == 0 else 'не работает'}")
    except:
        checks.append("❌ Docker: не доступен")
    try:
        r = subprocess.run(['docker', 'ps', '--format', '{{.Names}} {{.Status}}'],
                          capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            checks.append("✅ Контейнеры:")
            for line in r.stdout.strip().split('\n'):
                checks.append(f"   {line}")
        else:
            checks.append("⚠️ Контейнеры не запущены")
    except:
        checks.append("❌ Не удалось проверить контейнеры")
    disk = psutil.disk_usage('/')
    checks.append(f"{'✅' if disk.percent < 90 else '⚠️'} Диск: {disk.percent}% использовано")
    mem = psutil.virtual_memory()
    checks.append(f"{'✅' if mem.percent < 90 else '⚠️'} RAM: {mem.percent}% использовано")
    for f in ['config/settings.json', 'data/clients.json', 'data/nodes.json']:
        path = os.path.join('/opt/mtprotoserver', f)
        checks.append(f"{'✅' if os.path.exists(path) else '❌'} {f}")
    return JSONResponse({'status': 'ok', 'output': '\n'.join(checks)})

@app.get("/api/system/speedtest")
async def speed_test():
    try:
        import time
        start = time.time()
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{speed_download}',
                           'https://speed.cloudflare.com/__down?bytes=5000000'],
                          capture_output=True, text=True, timeout=30)
        download_speed = float(r.stdout) * 8 / 1000000 if r.stdout else 0
        start2 = time.time()
        r2 = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{speed_upload}',
                            '-X', 'POST', '-d', 'x' * 1000000,
                            'https://speed.cloudflare.com/__up'],
                           capture_output=True, text=True, timeout=30)
        upload_speed = float(r2.stdout) * 8 / 1000000 if r2.stdout else 0
        r3 = subprocess.run(['ping', '-c', '4', '-W', '2', '1.1.1.1'],
                           capture_output=True, text=True, timeout=10)
        ping = 'N/A'
        if r3.stdout:
            for line in r3.stdout.strip().split('\n'):
                if 'avg' in line or 'rtt' in line:
                    parts = line.split('/')
                    if len(parts) >= 5:
                        ping = parts[4]
                        break
        return JSONResponse({
            'status': 'ok',
            'download_mbps': round(download_speed, 2),
            'upload_mbps': round(upload_speed, 2),
            'ping_ms': ping
        })
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/set-adtag")
async def set_adtag(request: Request):
    form = await request.form()
    ad_tag = form.get('ad_tag', '')
    settings = get_settings()
    settings['ad_tag'] = ad_tag
    save_settings(settings)
    return JSONResponse({'status': 'ok', 'ad_tag': ad_tag})

@app.post("/api/system/rotate-domain")
async def rotate_domain(request: Request):
    form = await request.form()
    domain = form.get('domain', 'cloudflare.com')
    settings = get_settings()
    settings['fake_domain'] = domain
    save_settings(settings)
    return JSONResponse({'status': 'ok', 'domain': domain})

@app.post("/api/system/test-webhook")
async def test_webhook(request: Request):
    import requests as req
    form = await request.form()
    url = form.get('webhook_url', '')
    if not url:
        return JSONResponse({'status': 'error', 'message': 'URL required'}, status_code=400)
    try:
        r = req.post(url, json={'text': '🟢 MTProtoSERVER: Test notification works!'}, timeout=10)
        return JSONResponse({'status': 'ok', 'response_code': r.status_code})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/upload-logo")
async def upload_logo(request: Request):
    form = await request.form()
    logo_file = form.get('logo')
    if logo_file and hasattr(logo_file, 'read'):
        content = await logo_file.read()
        with open(LOGO_FILE, 'wb') as f:
            f.write(content)
        return JSONResponse({'status': 'ok'})
    return JSONResponse({'status': 'error', 'message': 'No file'}, status_code=400)

@app.get("/api/system/logo")
async def get_logo():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, 'rb') as f:
            return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")
    raise HTTPException(status_code=404)

@app.get("/api/qr")
async def generate_qr(text: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/api/status")
async def api_status():
    settings = get_settings()
    system = get_system_info()
    clients_data = get_clients()
    nodes_data = get_nodes()
    containers = get_docker_status()
    clients = clients_data.get('clients', [])
    nodes = nodes_data.get('nodes', [])
    return JSONResponse({
        'proxy_ip': settings.get('proxy_ip'),
        'clients_count': len(clients),
        'active_clients': len([c for c in clients if c.get('enabled')]),
        'nodes_count': len(nodes),
        'system': system,
        'containers': containers
    })

@app.get("/api/metrics")
async def api_metrics():
    clients_data = get_clients()
    clients = clients_data.get('clients', [])
    metrics = "# HELP mtproto_clients_total Total clients\n# TYPE mtproto_clients_total gauge\n"
    metrics += f"mtproto_clients_total {len(clients)}\n"
    metrics += "# HELP mtproto_clients_active Active clients\n# TYPE mtproto_clients_active gauge\n"
    metrics += f"mtproto_clients_active {len([c for c in clients if c.get('enabled')])}\n"
    for c in clients:
        metrics += f"# HELP mtproto_client_rx_bytes RX bytes for {c['label']}\n"
        metrics += f"# TYPE mtproto_client_rx_bytes counter\n"
        metrics += f'mtproto_client_rx_bytes{{client="{c["label"]}"}} {c.get("rx_bytes", 0)}\n'
    return HTMLResponse(content=metrics)

# =================== SECURITY API ===================

@app.get("/api/security/ip-lists")
async def get_ip_lists():
    settings = get_settings()
    return JSONResponse({
        'blacklist': settings.get('ip_blacklist', []),
        'whitelist': settings.get('ip_whitelist', [])
    })

@app.post("/api/security/blacklist/add")
async def add_to_blacklist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    bl = settings.get('ip_blacklist', [])
    if ip not in bl:
        bl.append(ip)
        settings['ip_blacklist'] = bl
        save_settings(settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/blacklist/remove")
async def remove_from_blacklist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    bl = settings.get('ip_blacklist', [])
    settings['ip_blacklist'] = [x for x in bl if x != ip]
    save_settings(settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/whitelist/add")
async def add_to_whitelist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    wl = settings.get('ip_whitelist', [])
    if ip not in wl:
        wl.append(ip)
        settings['ip_whitelist'] = wl
        save_settings(settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/whitelist/remove")
async def remove_from_whitelist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    wl = settings.get('ip_whitelist', [])
    settings['ip_whitelist'] = [x for x in wl if x != ip]
    save_settings(settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/firewall")
async def manage_firewall(request: Request):
    form = await request.form()
    port = form.get('port', '')
    action = form.get('action', 'allow')
    try:
        if action == 'allow':
            subprocess.run(['ufw', 'allow', str(port) + '/tcp'], capture_output=True, timeout=10)
        else:
            subprocess.run(['ufw', 'deny', str(port) + '/tcp'], capture_output=True, timeout=10)
        return JSONResponse({'status': 'ok'})
    except:
        return JSONResponse({'status': 'error', 'message': 'UFW unavailable'}, status_code=500)

@app.get("/api/security/firewall")
async def get_firewall_rules():
    try:
        r = subprocess.run(['ufw', 'status', 'numbered'], capture_output=True, text=True, timeout=10)
        rules = [line.strip() for line in r.stdout.strip().split('\n')[2:] if line.strip()] if r.stdout else []
        return JSONResponse({'rules': rules})
    except:
        return JSONResponse({'rules': []})

@app.post("/api/security/ratelimit")
async def set_ratelimit(request: Request):
    form = await request.form()
    rate = int(form.get('rate', 100))
    settings = get_settings()
    settings['rate_limit'] = rate
    save_settings(settings)
    return JSONResponse({'status': 'ok', 'rate': rate})

@app.get("/api/security/export")
async def export_configs():
    import zipfile
    import tempfile
    zip_path = tempfile.mktemp(suffix='.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk('/opt/mtprotoserver'):
            if 'backups' in root or '.git' in root:
                continue
            for f in files:
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, '/opt/mtprotoserver')
                zf.write(fp, arcname)
    def iterfile():
        with open(zip_path, 'rb') as f:
            yield from f
        os.unlink(zip_path)
    return StreamingResponse(iterfile(), media_type='application/zip',
                            headers={'Content-Disposition': 'attachment; filename=mtprotoserver-configs.zip'})
