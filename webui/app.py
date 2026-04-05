from fastapi import FastAPI, Request, HTTPException, status
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
import hashlib
import docker
import requests as req
import zipfile
import tempfile
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
AUTH_FILE = os.path.join(CONFIG_DIR, "auth.json")
BACKUPS_DIR = "/app/backups"
HOST_DIR = "/opt/mtprotoserver"

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
    s = load_json(SETTINGS_FILE)
    defaults = {
        'proxy_ip': '0.0.0.0', 'proxy_port': 443, 'fake_domain': 'cloudflare.com',
        'webui_port': 8080, 'proxy_count': 1, 'bot_enabled': False, 'bot_token': '',
        'admin_chat_id': '', 'socks5_enabled': False, 'socks5_port': 1080,
        'socks5_user': '', 'socks5_pass': '', 'http_proxy_enabled': False,
        'http_proxy_port': 3128, 'http_proxy_user': '', 'http_proxy_pass': '',
        'ad_tag': '', 'geoblock_countries': '', 'webhook_url': '',
        'auto_heal': True, 'auto_update': True, 'backup_enabled': True,
        'backup_interval': 'daily', 'monitor_interval': 300, 'geoblock': [],
        'ip_whitelist': [], 'ip_blacklist': [], 'rate_limit': 100,
    }
    for k, v in defaults.items():
        if k not in s: s[k] = v
    return s

def save_settings(data): save_json(SETTINGS_FILE, data)
def get_clients(): return load_json(CLIENTS_FILE)
def save_clients(data): save_json(CLIENTS_FILE, data)
def get_nodes(): return load_json(NODES_FILE)
def save_nodes(data): save_json(NODES_FILE, data)
def get_auth(): return load_json(AUTH_FILE)
def save_auth(data): save_json(AUTH_FILE, data)

def get_proxy_link(ip, port, secret):
    return f"tg://proxy?server={ip}&port={port}&secret={secret}"

def get_docker_client():
    try:
        return docker.from_env()
    except:
        return None

def run_compose(args, timeout=60):
    try:
        r = subprocess.run(['docker', 'compose'] + args, capture_output=True, text=True, cwd=HOST_DIR, timeout=timeout)
        return r.stdout if r.returncode == 0 else r.stderr
    except Exception as e:
        return str(e)

def get_docker_status():
    containers = []
    try:
        r = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.Ports}}'],
                          capture_output=True, text=True, timeout=10)
        if r.stdout.strip():
            for line in r.stdout.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 3:
                    containers.append({'name': parts[0], 'status': parts[1], 'ports': parts[2]})
    except: pass
    return containers

def get_system_info():
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            'cpu_percent': psutil.cpu_percent(), 'memory_percent': mem.percent,
            'memory_total_gb': round(mem.total / (1024**3), 1), 'memory_used_gb': round(mem.used / (1024**3), 1),
            'disk_percent': disk.percent, 'disk_total_gb': round(disk.total / (1024**3), 1),
            'disk_used_gb': round(disk.used / (1024**3), 1),
        }
    except:
        return {'cpu_percent': 0, 'memory_percent': 0, 'memory_total_gb': 0, 'memory_used_gb': 0, 'disk_percent': 0, 'disk_total_gb': 0, 'disk_used_gb': 0}

def format_bytes(b):
    if b == 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024: return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def common_context(request: Request):
    return {
        'settings': get_settings(), 'has_logo': os.path.exists(LOGO_FILE),
        'lang': 'ru', 'now': datetime.now().strftime('%Y-%m-%d')
    }

# =================== AUTH MIDDLEWARE ===================

PROTECTED_PATHS = ['/clients', '/nodes', '/stats', '/settings', '/security', '/logs', '/backup', '/socks5', '/http-proxy', '/mtproto']

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path == '/login' or path.startswith('/static') or path.startswith('/api/auth') or path == '/api/qr' or path == '/api/system/logo':
        return await call_next(request)
    if path in PROTECTED_PATHS or path == '/':
        auth = get_auth()
        if auth.get('token'):
            session_token = request.cookies.get('auth_token', '')
            if session_token != auth['token']:
                if path == '/':
                    return RedirectResponse(url='/login', status_code=302)
                return RedirectResponse(url='/login', status_code=302)
    return await call_next(request)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})

@app.post("/api/auth/login")
async def api_login(request: Request):
    form = await request.form()
    password = form.get('password', '')
    auth = get_auth()
    if not auth.get('token'):
        return JSONResponse({'status': 'error', 'message': 'Пароль не установлен'})
    if password == auth['token']:
        resp = JSONResponse({'status': 'ok'})
        resp.set_cookie('auth_token', password, httponly=True, max_age=86400*30)
        return resp
    return JSONResponse({'status': 'error', 'message': 'Неверный пароль'}, status_code=401)

@app.post("/api/auth/logout")
async def api_logout():
    resp = JSONResponse({'status': 'ok'})
    resp.delete_cookie('auth_token')
    return resp

# =================== PAGES ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    ctx = common_context(request)
    clients_data = get_clients()
    nodes_data = get_nodes()
    system = get_system_info()
    containers = get_docker_status()
    clients = clients_data.get('clients', [])
    nodes = nodes_data.get('nodes', [])
    active = len([c for c in clients if c.get('enabled', True)])
    total_rx = sum(c.get('rx_bytes', 0) for c in clients)
    total_tx = sum(c.get('tx_bytes', 0) for c in clients)
    ctx.update({
        'clients': clients, 'nodes': nodes, 'clients_count': len(clients), 'active_clients': active,
        'nodes_count': len(nodes), 'total_rx': format_bytes(total_rx), 'total_tx': format_bytes(total_tx),
        'system': system, 'containers': containers
    })
    return templates.TemplateResponse("dashboard.html", ctx)

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    ctx = common_context(request)
    ctx.update({'clients': get_clients().get('clients', []), 'nodes': get_nodes().get('nodes', [])})
    return templates.TemplateResponse("clients.html", ctx)

@app.get("/nodes", response_class=HTMLResponse)
async def nodes_page(request: Request):
    ctx = common_context(request)
    ctx.update({'nodes': get_nodes().get('nodes', [])})
    return templates.TemplateResponse("nodes.html", ctx)

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    ctx = common_context(request)
    ctx.update({'clients': get_clients().get('clients', []), 'system': get_system_info()})
    return templates.TemplateResponse("stats.html", ctx)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    ctx = common_context(request)
    ctx.update({'auth': get_auth()})
    return templates.TemplateResponse("settings.html", ctx)

@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    return templates.TemplateResponse("security.html", common_context(request))

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", common_context(request))

@app.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request):
    return templates.TemplateResponse("backup.html", common_context(request))

@app.get("/socks5", response_class=HTMLResponse)
async def socks5_page(request: Request):
    return templates.TemplateResponse("socks5.html", common_context(request))

@app.get("/http-proxy", response_class=HTMLResponse)
async def http_proxy_page(request: Request):
    return templates.TemplateResponse("http_proxy.html", common_context(request))

@app.get("/mtproto", response_class=HTMLResponse)
async def mtproto_page(request: Request):
    return templates.TemplateResponse("mtproto.html", common_context(request))

# =================== CLIENTS API ===================

@app.post("/api/clients/add")
async def add_client(request: Request):
    form = await request.form()
    label = form.get('label', 'client')
    node_id = int(form.get('node_id', 0) or 0)
    traffic_limit_gb = float(form.get('traffic_limit_gb', 0) or 0)
    device_limit = int(form.get('device_limit', 0) or 0)
    expiry_days = int(form.get('expiry_days', 0) or 0)
    settings = get_settings()
    cd = get_clients()
    clients = cd.get('clients', [])
    next_id = cd.get('next_id', 1)
    domain = form.get('domain', settings.get('fake_domain', 'cloudflare.com'))
    secret = f"ee{sec.token_hex(14)}{domain.encode().hex()}"
    port = 443 + next_id
    expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d') if expiry_days > 0 else ''
    clients.append({
        'id': next_id, 'label': label, 'node_id': node_id, 'port': port, 'domain': domain,
        'secret': secret, 'enabled': True, 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'traffic_limit_gb': traffic_limit_gb, 'device_limit': device_limit, 'expiry_date': expiry_date,
        'auto_reset': form.get('auto_reset', 'never'), 'rx_bytes': 0, 'tx_bytes': 0,
        'unique_ips': 0, 'connections': 0, 'history': []
    })
    cd['clients'] = clients
    cd['next_id'] = next_id + 1
    save_clients(cd)
    # Auto-open firewall
    try: subprocess.run(['ufw', 'allow', str(port) + '/tcp'], capture_output=True, timeout=10)
    except: pass
    return JSONResponse({'status': 'ok', 'secret': secret, 'link': get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), port, secret), 'port': port})

@app.post("/api/clients/{cid}/toggle")
async def toggle_client(cid: int):
    cd = get_clients()
    for c in cd.get('clients', []):
        if c['id'] == cid: c['enabled'] = not c.get('enabled', True); break
    save_clients(cd)
    return JSONResponse({'status': 'ok'})

@app.post("/api/clients/{cid}/delete")
async def delete_client(cid: int):
    cd = get_clients()
    cd['clients'] = [c for c in cd.get('clients', []) if c['id'] != cid]
    save_clients(cd)
    return JSONResponse({'status': 'ok'})

@app.post("/api/clients/{cid}/rotate")
async def rotate_client(cid: int):
    cd = get_clients()
    settings = get_settings()
    for c in cd.get('clients', []):
        if c['id'] == cid:
            c['secret'] = f"ee{sec.token_hex(14)}{c.get('domain', 'cloudflare.com').encode().hex()}"; break
    save_clients(cd)
    return JSONResponse({'status': 'ok', 'secret': c['secret'], 'link': get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), c['port'], c['secret'])})

@app.post("/api/clients/{cid}/reset-traffic")
async def reset_traffic(cid: int):
    cd = get_clients()
    for c in cd.get('clients', []):
        if c['id'] == cid: c['rx_bytes'] = 0; c['tx_bytes'] = 0; break
    save_clients(cd)
    return JSONResponse({'status': 'ok'})

@app.get("/api/clients/{cid}/history")
async def get_client_history(cid: int):
    cd = get_clients()
    for c in cd.get('clients', []):
        if c['id'] == cid: return JSONResponse({'history': c.get('history', [])})
    return JSONResponse({'history': []})

# =================== NODES API ===================

@app.post("/api/nodes/add")
async def add_node(request: Request):
    form = await request.form()
    nd = get_nodes()
    nodes = nd.get('nodes', [])
    next_id = nd.get('next_id', 1)
    nodes.append({
        'id': next_id, 'name': form.get('name', 'node'), 'ip': form.get('ip', ''),
        'port': int(form.get('port', 9876) or 9876), 'country': form.get('country', '🌍'),
        'token': form.get('token', ''), 'auth_type': form.get('auth_type', 'token'),
        'ssh_user': form.get('ssh_user', ''), 'ssh_pass': form.get('ssh_pass', ''),
        'ssh_key': form.get('ssh_key', ''), 'enabled': True,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'last_ping': '', 'status': 'unknown'
    })
    nd['nodes'] = nodes; nd['next_id'] = next_id + 1
    save_nodes(nd)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{nid}/toggle")
async def toggle_node(nid: int):
    nd = get_nodes()
    for n in nd.get('nodes', []):
        if n['id'] == nid: n['enabled'] = not n.get('enabled', True); break
    save_nodes(nd)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{nid}/delete")
async def delete_node(nid: int):
    nd = get_nodes()
    nd['nodes'] = [n for n in nd.get('nodes', []) if n['id'] != nid]
    save_nodes(nd)
    return JSONResponse({'status': 'ok'})

@app.post("/api/nodes/{nid}/ping")
async def ping_node(nid: int):
    nd = get_nodes()
    for n in nd.get('nodes', []):
        if n['id'] == nid:
            try:
                r = req.get(f"http://{n['ip']}:{n['port']}/health", timeout=5)
                n['status'] = 'online' if r.status_code == 200 else 'offline'
            except: n['status'] = 'offline'
            n['last_ping'] = datetime.now().strftime('%H:%M:%S')
            save_nodes(nd)
            return JSONResponse({'status': 'ok', 'node_status': n['status'], 'last_ping': n['last_ping']})
    return JSONResponse({'status': 'error', 'message': 'Нода не найдена'}, status_code=404)

@app.post("/api/nodes/{nid}/sync")
async def sync_node(nid: int):
    nd = get_nodes()
    cd = get_clients()
    for n in nd.get('nodes', []):
        if n['id'] == nid:
            try:
                r = req.get(f"http://{n['ip']}:{n['port']}/clients", headers={'x-token': n['token']}, timeout=10)
                remote = r.json().get('clients', [])
                local = cd.get('clients', [])
                for rc in remote:
                    found = False
                    for lc in local:
                        if lc['label'] == rc.get('label', ''):
                            lc.update({'rx_bytes': rc.get('rx_bytes', 0), 'tx_bytes': rc.get('tx_bytes', 0), 'unique_ips': rc.get('unique_ips', 0), 'status': rc.get('status', 'unknown')})
                            found = True; break
                    if not found: local.append(rc)
                cd['clients'] = local; save_clients(cd)
                return JSONResponse({'status': 'ok', 'synced': len(remote)})
            except Exception as e:
                return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)
    return JSONResponse({'status': 'error', 'message': 'Нода не найдена'}, status_code=404)

# =================== PROXY MANAGEMENT (SOCKS5/HTTP) ===================

@app.post("/api/proxies/socks5/create")
async def create_socks5(request: Request):
    form = await request.form()
    port = int(form.get('port', 1080) or 1080)
    user = form.get('user', 'proxyuser')
    password = form.get('password', sec.token_hex(8))
    settings = get_settings()
    settings['socks5_enabled'] = True
    settings['socks5_port'] = port
    settings['socks5_user'] = user
    settings['socks5_pass'] = password
    save_settings(settings)
    # Create config
    os.makedirs(f"{HOST_DIR}/config", exist_ok=True)
    with open(f"{HOST_DIR}/config/socks5.conf", 'w') as f:
        f.write(f"""logoutput: stderr
internal: 0.0.0.0 port = 1080
external: eth0
clientmethod: none
socksmethod: username
user.privileged: root
user.notprivileged: sockd
user.libwrap: nobody
client pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 }}
socks pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 user: {user} password: {password} }}
""")
    # Add to docker-compose
    dc_file = f"{HOST_DIR}/docker-compose.yml"
    if os.path.exists(dc_file):
        with open(dc_file, 'r') as f: content = f.read()
        if 'socks5:' not in content:
            with open(dc_file, 'a') as f:
                f.write(f"""
  socks5:
    image: vimagick/dante
    container_name: mtproto-socks5
    restart: unless-stopped
    ports:
      - "{port}:1080"
    volumes:
      - ./config/socks5.conf:/etc/sockd.conf:ro
    cap_add:
      - NET_ADMIN
    networks:
      - mtproto-net
""")
    # Open port
    try: subprocess.run(['ufw', 'allow', str(port) + '/tcp'], capture_output=True, timeout=10)
    except: pass
    # Start container
    run_compose(['up', '-d', 'socks5'])
    return JSONResponse({'status': 'ok', 'port': port, 'user': user, 'password': password})

@app.post("/api/proxies/http/create")
async def create_http(request: Request):
    form = await request.form()
    port = int(form.get('port', 3128) or 3128)
    user = form.get('user', 'proxyuser')
    password = form.get('password', sec.token_hex(8))
    settings = get_settings()
    settings['http_proxy_enabled'] = True
    settings['http_proxy_port'] = port
    settings['http_proxy_user'] = user
    settings['http_proxy_pass'] = password
    save_settings(settings)
    os.makedirs(f"{HOST_DIR}/config", exist_ok=True)
    with open(f"{HOST_DIR}/config/squid.conf", 'w') as f:
        f.write(f"""http_port 3128
cache_dir ufs /var/spool/squid 100 16 256
coredump_dir /var/spool/squid
auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic children 5
auth_param basic realm Squid Proxy
acl auth_users proxy_auth REQUIRED
http_access allow auth_users
http_access deny all
""")
    dc_file = f"{HOST_DIR}/docker-compose.yml"
    if os.path.exists(dc_file):
        with open(dc_file, 'r') as f: content = f.read()
        if 'http-proxy:' not in content:
            with open(dc_file, 'a') as f:
                f.write(f"""
  http-proxy:
    image: sameersbn/squid:latest
    container_name: mtproto-http-proxy
    restart: unless-stopped
    ports:
      - "{port}:3128"
    volumes:
      - ./config/squid.conf:/etc/squid/squid.conf:ro
      - ./data/squid-cache:/var/spool/squid
    networks:
      - mtproto-net
""")
    try: subprocess.run(['ufw', 'allow', str(port) + '/tcp'], capture_output=True, timeout=10)
    except: pass
    run_compose(['up', '-d', 'http-proxy'])
    return JSONResponse({'status': 'ok', 'port': port, 'user': user, 'password': password})

@app.post("/api/proxies/socks5/delete")
async def delete_socks5():
    settings = get_settings()
    settings['socks5_enabled'] = False
    save_settings(settings)
    run_compose(['down', 'socks5'])
    return JSONResponse({'status': 'ok'})

@app.post("/api/proxies/http/delete")
async def delete_http():
    settings = get_settings()
    settings['http_proxy_enabled'] = False
    save_settings(settings)
    run_compose(['down', 'http-proxy'])
    return JSONResponse({'status': 'ok'})

# =================== SYSTEM API ===================

@app.post("/api/system/restart")
async def restart_system():
    return JSONResponse({'status': 'ok', 'message': run_compose(['restart'])})

@app.post("/api/system/restart-container")
async def restart_container(request: Request):
    form = await request.form()
    name = form.get('name', '')
    if name: return JSONResponse({'status': 'ok', 'message': run_compose(['restart', name])})
    return JSONResponse({'status': 'error'}, status_code=400)

@app.get("/api/system/logs")
async def get_logs(lines: int = 100):
    return JSONResponse({'status': 'ok', 'logs': run_compose(['logs', '--tail', str(lines)])})

@app.post("/api/system/backup")
async def create_backup():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = f'backup_{ts}.tar.gz'
    fp = os.path.join(BACKUPS_DIR, fn)
    try:
        subprocess.run(['tar', '-czf', fp, '-C', HOST_DIR, 'config', 'data', 'docker-compose.yml'], capture_output=True, timeout=30)
        sz = os.path.getsize(fp)
        return JSONResponse({'status': 'ok', 'filename': fn, 'size': f"{sz/1024:.1f} KB" if sz < 1024*1024 else f"{sz/(1024*1024):.1f} MB"})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.get("/api/system/backups")
async def list_backups():
    backups = []
    if os.path.exists(BACKUPS_DIR):
        for f in sorted(os.listdir(BACKUPS_DIR), reverse=True):
            if f.endswith('.tar.gz'):
                sz = os.path.getsize(os.path.join(BACKUPS_DIR, f))
                backups.append({'name': f, 'size': f"{sz/1024:.1f} KB" if sz < 1024*1024 else f"{sz/(1024*1024):.1f} MB"})
    return JSONResponse({'backups': backups})

@app.post("/api/system/restore")
async def restore_backup(request: Request):
    form = await request.form()
    fp = os.path.join(BACKUPS_DIR, form.get('name', ''))
    if not os.path.exists(fp): return JSONResponse({'status': 'error', 'message': 'Не найден'}, status_code=404)
    try:
        subprocess.run(['tar', '-xzf', fp, '-C', HOST_DIR], capture_output=True, timeout=30)
        return JSONResponse({'status': 'ok'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/delete-backup")
async def delete_backup(request: Request):
    fp = os.path.join(BACKUPS_DIR, (await request.form()).get('name', ''))
    if os.path.exists(fp): os.remove(fp)
    return JSONResponse({'status': 'ok'})

@app.get("/api/system/health")
async def health_check():
    checks = []
    dc = get_docker_client()
    if dc:
        checks.append("✅ Docker: работает")
        try:
            containers = dc.containers.list(all=True)
            if containers:
                checks.append("✅ Контейнеры:")
                for c in containers:
                    checks.append(f"   {c.name}: {c.status}")
            else: checks.append("⚠️ Контейнеры не запущены")
        except: checks.append("❌ Не удалось проверить контейнеры")
    else:
        checks.append("❌ Docker: не доступен")
    disk = psutil.disk_usage('/')
    checks.append(f"{'✅' if disk.percent < 90 else '⚠️'} Диск: {disk.percent}% использовано")
    mem = psutil.virtual_memory()
    checks.append(f"{'✅' if mem.percent < 90 else '⚠️'} RAM: {mem.percent}% использовано")
    for f in ['config/settings.json', 'data/clients.json', 'data/nodes.json']:
        checks.append(f"{'✅' if os.path.exists(os.path.join('/app', f)) else '❌'} {f}")
    return JSONResponse({'status': 'ok', 'output': '\n'.join(checks)})

@app.get("/api/system/speedtest")
async def speed_test():
    try:
        start = time.time()
        r = req.get('https://speed.cloudflare.com/__down?bytes=5000000', timeout=30)
        dl_speed = len(r.content) / (time.time() - start) * 8 / 1000000
        start2 = time.time()
        r2 = req.post('https://speed.cloudflare.com/__up', data=b'x' * 1000000, timeout=30)
        ul_speed = 1000000 / (time.time() - start2) * 8 / 1000000
        start3 = time.time()
        req.get('https://1.1.1.1', timeout=5)
        ping_ms = round((time.time() - start3) * 1000, 1)
        return JSONResponse({'status': 'ok', 'download_mbps': round(dl_speed, 2), 'upload_mbps': round(ul_speed, 2), 'ping_ms': ping_ms})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/update")
async def update_system():
    msg = run_compose(['pull'])
    msg += run_compose(['up', '-d', '--build', '--force-recreate'])
    return JSONResponse({'status': 'ok', 'message': msg})

@app.post("/api/system/set-adtag")
async def set_adtag(request: Request):
    form = await request.form()
    s = get_settings(); s['ad_tag'] = form.get('ad_tag', ''); save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.post("/api/system/rotate-domain")
async def rotate_domain(request: Request):
    form = await request.form()
    s = get_settings(); s['fake_domain'] = form.get('domain', 'cloudflare.com'); save_settings(s)
    return JSONResponse({'status': 'ok', 'domain': s['fake_domain']})

@app.post("/api/system/test-webhook")
async def test_webhook(request: Request):
    form = await request.form()
    url = form.get('webhook_url', '')
    if not url: return JSONResponse({'status': 'error'}, status_code=400)
    try:
        r = req.post(url, json={'text': '🟢 MTProtoSERVER: Тест работает!'}, timeout=10)
        return JSONResponse({'status': 'ok', 'response_code': r.status_code})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/upload-logo")
async def upload_logo(request: Request):
    form = await request.form()
    f = form.get('logo')
    if f and hasattr(f, 'read'):
        with open(LOGO_FILE, 'wb') as fw: fw.write(await f.read())
        return JSONResponse({'status': 'ok'})
    return JSONResponse({'status': 'error'}, status_code=400)

@app.get("/api/system/logo")
async def get_logo():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, 'rb') as f: return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")
    raise HTTPException(status_code=404)

@app.get("/api/qr")
async def generate_qr(text: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/api/status")
async def api_status():
    s = get_settings(); cd = get_clients(); nd = get_nodes()
    clients = cd.get('clients', []); nodes = nd.get('nodes', [])
    return JSONResponse({
        'proxy_ip': s.get('proxy_ip'), 'clients_count': len(clients),
        'active_clients': len([c for c in clients if c.get('enabled')]),
        'nodes_count': len(nodes), 'system': get_system_info(), 'containers': get_docker_status()
    })

@app.get("/api/metrics")
async def api_metrics():
    cd = get_clients(); clients = cd.get('clients', [])
    m = f"# HELP mtproto_clients_total Total clients\n# TYPE mtproto_clients_total gauge\nmtproto_clients_total {len(clients)}\n"
    m += f"# HELP mtproto_clients_active Active clients\n# TYPE mtproto_clients_active gauge\nmtproto_clients_active {len([c for c in clients if c.get('enabled')])}\n"
    for c in clients:
        m += f"# HELP mtproto_client_rx RX for {c['label']}\n# TYPE mtproto_client_rx counter\nmtproto_client_rx{{client=\"{c['label']}\"}} {c.get('rx_bytes', 0)}\n"
    return HTMLResponse(content=m)

# =================== SECURITY API ===================

@app.get("/api/security/ip-lists")
async def get_ip_lists():
    s = get_settings()
    return JSONResponse({'blacklist': s.get('ip_blacklist', []), 'whitelist': s.get('ip_whitelist', [])})

@app.post("/api/security/blacklist/add")
async def add_blacklist(request: Request):
    form = await request.form(); ip = form.get('ip', '')
    s = get_settings(); bl = s.get('ip_blacklist', [])
    if ip not in bl: bl.append(ip); s['ip_blacklist'] = bl; save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/blacklist/remove")
async def remove_blacklist(request: Request):
    form = await request.form(); ip = form.get('ip', '')
    s = get_settings(); s['ip_blacklist'] = [x for x in s.get('ip_blacklist', []) if x != ip]; save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/whitelist/add")
async def add_whitelist(request: Request):
    form = await request.form(); ip = form.get('ip', '')
    s = get_settings(); wl = s.get('ip_whitelist', [])
    if ip not in wl: wl.append(ip); s['ip_whitelist'] = wl; save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/whitelist/remove")
async def remove_whitelist(request: Request):
    form = await request.form(); ip = form.get('ip', '')
    s = get_settings(); s['ip_whitelist'] = [x for x in s.get('ip_whitelist', []) if x != ip]; save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/firewall")
async def manage_firewall(request: Request):
    form = await request.form(); port = form.get('port', ''); action = form.get('action', 'allow')
    try:
        cmd = 'allow' if action == 'allow' else 'deny'
        subprocess.run(['ufw', cmd, str(port) + '/tcp'], capture_output=True, timeout=10)
        return JSONResponse({'status': 'ok'})
    except: return JSONResponse({'status': 'error', 'message': 'UFW недоступен'}, status_code=500)

@app.get("/api/security/firewall")
async def get_firewall_rules():
    try:
        r = subprocess.run(['ufw', 'status', 'numbered'], capture_output=True, text=True, timeout=10)
        rules = [l.strip() for l in r.stdout.strip().split('\n')[2:] if l.strip()] if r.stdout else []
        return JSONResponse({'rules': rules})
    except: return JSONResponse({'rules': []})

@app.post("/api/security/ratelimit")
async def set_ratelimit(request: Request):
    form = await request.form()
    s = get_settings(); s['rate_limit'] = int(form.get('rate', 100)); save_settings(s)
    return JSONResponse({'status': 'ok'})

@app.get("/api/security/export")
async def export_configs():
    zip_path = tempfile.mktemp(suffix='.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(HOST_DIR):
            if 'backups' in root or '.git' in root: continue
            for f in files:
                fp = os.path.join(root, f)
                zf.write(fp, os.path.relpath(fp, HOST_DIR))
    def iterfile():
        with open(zip_path, 'rb') as f: yield from f
        os.unlink(zip_path)
    return StreamingResponse(iterfile(), media_type='application/zip', headers={'Content-Disposition': 'attachment; filename=mtprotoserver-configs.zip'})
