from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import json
import os
import subprocess
import secrets as sec
import psutil
import io
import qrcode

app = FastAPI(title="MTProtoSERVER Web UI")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "/app/data"
CONFIG_DIR = "/app/config"
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROXIES_FILE = os.path.join(DATA_DIR, "proxies.json")

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_settings():
    return load_json(SETTINGS_FILE)

def get_users():
    return load_json(USERS_FILE)

def save_users(data):
    save_json(USERS_FILE, data)

def get_proxies():
    return load_json(PROXIES_FILE)

def save_proxies(data):
    save_json(PROXIES_FILE, data)

def get_proxy_link(ip, port, secret):
    return f"tg://proxy?server={ip}&port={port}&secret={secret}"

def run_docker_cmd(args):
    try:
        result = subprocess.run(
            ['docker', 'compose'] + args,
            capture_output=True, text=True, cwd='/opt/mtprotoserver',
            timeout=30
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
                    containers.append({
                        'name': parts[0],
                        'status': parts[1],
                        'ports': parts[2]
                    })
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

# =================== PAGES ===================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    users_data = get_users()
    proxies_data = get_proxies()
    system = get_system_info()
    containers = get_docker_status()
    users = users_data.get('users', [])
    proxies = proxies_data.get('proxies', [])
    active_users = len([u for u in users if u.get('enabled', True)])
    active_proxies = len([p for p in proxies if p.get('enabled', True)])
    total_traffic = sum(u.get('traffic_in', 0) + u.get('traffic_out', 0) for u in users)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
        "users_count": len(users),
        "active_users": active_users,
        "total_traffic": total_traffic,
        "system": system,
        "proxies": proxies,
        "active_proxies": active_proxies,
        "proxy_count": len(proxies),
        "containers": containers
    })

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    users_data = get_users()
    proxies_data = get_proxies()
    users = users_data.get('users', [])
    proxies = proxies_data.get('proxies', [])
    settings = get_settings()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "proxies": proxies,
        "settings": settings
    })

@app.get("/proxies", response_class=HTMLResponse)
async def proxies_page(request: Request):
    proxies_data = get_proxies()
    proxies = proxies_data.get('proxies', [])
    settings = get_settings()
    return templates.TemplateResponse("proxies.html", {
        "request": request,
        "proxies": proxies,
        "settings": settings
    })

@app.get("/socks5", response_class=HTMLResponse)
async def socks5_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("socks5.html", {
        "request": request,
        "settings": settings
    })

@app.get("/http-proxy", response_class=HTMLResponse)
async def http_proxy_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("http_proxy.html", {
        "request": request,
        "settings": settings
    })

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    users_data = get_users()
    proxies_data = get_proxies()
    users = users_data.get('users', [])
    proxies = proxies_data.get('proxies', [])
    system = get_system_info()
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "users": users,
        "proxies": proxies,
        "system": system
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {
        "request": request
    })

@app.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request):
    return templates.TemplateResponse("backup.html", {
        "request": request
    })

@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("security.html", {
        "request": request,
        "settings": settings
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings
    })

@app.get("/diagnostics", response_class=HTMLResponse)
async def diagnostics_page(request: Request):
    system = get_system_info()
    containers = get_docker_status()
    logs = run_docker_cmd(['logs', '--tail', '50'])
    return templates.TemplateResponse("diagnostics.html", {
        "request": request,
        "system": system,
        "containers": containers,
        "logs": logs
    })

# =================== API: USERS ===================

@app.post("/api/users/add")
async def add_user(request: Request):
    form = await request.form()
    label = form.get('label', 'user')
    proxy_id = int(form.get('proxy_id', 1))
    proxies_data = get_proxies()
    proxies = proxies_data.get('proxies', [])

    target_proxy = None
    for p in proxies:
        if p['id'] == proxy_id:
            target_proxy = p
            break

    if not target_proxy:
        return JSONResponse({'status': 'error', 'message': 'Прокси не найден'}, status_code=400)

    users_data = get_users()
    users = users_data.get('users', [])
    next_id = users_data.get('next_id', 1)

    new_secret = sec.token_hex(16)

    new_user = {
        'id': next_id,
        'label': label,
        'proxy_id': proxy_id,
        'secret': new_secret,
        'enabled': True,
        'created_at': 'now',
        'max_connections': 0,
        'max_ips': 0,
        'data_quota': '0',
        'expires': '',
        'traffic_in': 0,
        'traffic_out': 0,
        'connections': 0
    }

    users.append(new_user)
    users_data['users'] = users
    users_data['next_id'] = next_id + 1
    save_users(users_data)

    link = get_proxy_link(
        get_settings().get('proxy_ip', '0.0.0.0'),
        target_proxy['port'],
        target_proxy['secret']
    )
    return JSONResponse({'status': 'ok', 'secret': new_secret, 'link': link})

@app.post("/api/users/{user_id}/toggle")
async def toggle_user(user_id: int):
    users_data = get_users()
    for u in users_data.get('users', []):
        if u['id'] == user_id:
            u['enabled'] = not u.get('enabled', True)
            break
    save_users(users_data)
    return JSONResponse({'status': 'ok', 'enabled': u['enabled']})

@app.post("/api/users/{user_id}/delete")
async def delete_user(user_id: int):
    users_data = get_users()
    users_data['users'] = [u for u in users_data.get('users', []) if u['id'] != user_id]
    save_users(users_data)
    return JSONResponse({'status': 'ok'})

# =================== API: PROXIES ===================

@app.post("/api/proxies/add")
async def add_proxy(request: Request):
    form = await request.form()
    label = form.get('label', 'proxy')
    port = int(form.get('port', 443))
    domain = form.get('domain', 'cloudflare.com')

    proxies_data = get_proxies()
    proxies = proxies_data.get('proxies', [])
    next_id = proxies_data.get('next_id', 1)

    domain_hex = domain.encode().hex()
    random_part = sec.token_hex(14)
    secret = f"ee{random_part}{domain_hex}"

    new_proxy = {
        'id': next_id,
        'label': label,
        'port': port,
        'domain': domain,
        'secret': secret,
        'enabled': True,
        'created_at': 'now',
        'connections': 0,
        'traffic_in': 0,
        'traffic_out': 0
    }

    proxies.append(new_proxy)
    proxies_data['proxies'] = proxies
    proxies_data['next_id'] = next_id + 1
    save_proxies(proxies_data)

    settings = get_settings()
    settings['proxy_count'] = len(proxies)
    save_json(SETTINGS_FILE, settings)

    link = get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), port, secret)
    return JSONResponse({'status': 'ok', 'secret': secret, 'link': link})

@app.post("/api/proxies/{proxy_id}/toggle")
async def toggle_proxy(proxy_id: int):
    proxies_data = get_proxies()
    for p in proxies_data.get('proxies', []):
        if p['id'] == proxy_id:
            p['enabled'] = not p.get('enabled', True)
            break
    save_proxies(proxies_data)
    return JSONResponse({'status': 'ok', 'enabled': p['enabled']})

@app.post("/api/proxies/{proxy_id}/delete")
async def delete_proxy(proxy_id: int):
    proxies_data = get_proxies()
    proxies_data['proxies'] = [p for p in proxies_data.get('proxies', []) if p['id'] != proxy_id]
    settings = get_settings()
    settings['proxy_count'] = len(proxies_data['proxies'])
    save_json(SETTINGS_FILE, settings)
    save_proxies(proxies_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/proxies/{proxy_id}/rotate-secret")
async def rotate_secret(proxy_id: int):
    proxies_data = get_proxies()
    for p in proxies_data.get('proxies', []):
        if p['id'] == proxy_id:
            domain_hex = p['domain'].encode().hex()
            random_part = sec.token_hex(14)
            p['secret'] = f"ee{random_part}{domain_hex}"
            break
    save_proxies(proxies_data)
    settings = get_settings()
    link = get_proxy_link(settings.get('proxy_ip', '0.0.0.0'), p['port'], p['secret'])
    return JSONResponse({'status': 'ok', 'secret': p['secret'], 'link': link})

# =================== API: SYSTEM ===================

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

@app.post("/api/system/set-adtag")
async def set_adtag(request: Request):
    form = await request.form()
    ad_tag = form.get('ad_tag', '')
    settings = get_settings()
    settings['ad_tag'] = ad_tag
    save_json(SETTINGS_FILE, settings)
    return JSONResponse({'status': 'ok', 'ad_tag': ad_tag})

@app.post("/api/system/rotate-domain")
async def rotate_domain(request: Request):
    form = await request.form()
    domain = form.get('domain', 'cloudflare.com')
    settings = get_settings()
    settings['fake_domain'] = domain
    save_json(SETTINGS_FILE, settings)
    return JSONResponse({'status': 'ok', 'domain': domain})

@app.get("/api/system/logs")
async def get_logs(lines: int = 100):
    logs = run_docker_cmd(['logs', '--tail', str(lines)])
    return JSONResponse({'status': 'ok', 'logs': logs})

@app.get("/api/status")
async def api_status():
    settings = get_settings()
    system = get_system_info()
    users_data = get_users()
    proxies_data = get_proxies()
    containers = get_docker_status()
    users = users_data.get('users', [])
    proxies = proxies_data.get('proxies', [])
    return JSONResponse({
        'proxy_ip': settings.get('proxy_ip'),
        'proxy_count': len(proxies),
        'active_proxies': len([p for p in proxies if p.get('enabled')]),
        'users_count': len(users),
        'active_users': len([u for u in users if u.get('enabled')]),
        'system': system,
        'containers': containers,
        'socks5_enabled': settings.get('socks5_enabled', False),
        'socks5_port': settings.get('socks5_port'),
        'ad_tag': settings.get('ad_tag', ''),
        'geoblock': settings.get('geoblock_countries', '')
    })

@app.get("/api/metrics")
async def api_metrics():
    users_data = get_users()
    proxies_data = get_proxies()
    users = users_data.get('users', [])
    proxies = proxies_data.get('proxies', [])
    metrics = "# HELP mtproto_proxies_total Total proxies\n# TYPE mtproto_proxies_total gauge\n"
    metrics += f"mtproto_proxies_total {len(proxies)}\n"
    metrics += "# HELP mtproto_users_total Total users\n# TYPE mtproto_users_total gauge\n"
    metrics += f"mtproto_users_total {len(users)}\n"
    metrics += "# HELP mtproto_users_active Active users\n# TYPE mtproto_users_active gauge\n"
    metrics += f"mtproto_users_active {len([u for u in users if u.get('enabled')])}\n"
    for u in users:
        metrics += f"# HELP mtproto_user_traffic_in Traffic in for {u['label']}\n"
        metrics += f"# TYPE mtproto_user_traffic_in counter\n"
        metrics += f'mtproto_user_traffic_in{{user="{u["label"]}"}} {u.get("traffic_in", 0)}\n'
    return HTMLResponse(content=metrics)

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

@app.post("/api/socks5/add-user")
async def add_socks5_user(request: Request):
    form = await request.form()
    user = form.get('user', '')
    password = form.get('pass', '')
    if not user or not password:
        return JSONResponse({'status': 'error', 'message': 'Логин и пароль обязательны'}, status_code=400)

    socks5_conf = '/opt/mtprotoserver/config/socks5.conf'
    if os.path.exists(socks5_conf):
        with open(socks5_conf, 'r') as f:
            content = f.read()
        new_rule = f"""socks pass {{
    from: 0.0.0.0/0 to: 0.0.0.0/0
    user: {user}
    password: {password}
}}
"""
        content = content.rstrip() + '\n' + new_rule
        with open(socks5_conf, 'w') as f:
            f.write(content)
        return JSONResponse({'status': 'ok', 'user': user})
    return JSONResponse({'status': 'error', 'message': 'SOCKS5 не установлен'}, status_code=400)

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
    backup_dir = '/opt/mtprotoserver/backups'
    filepath = os.path.join(backup_dir, name)
    if not os.path.exists(filepath):
        return JSONResponse({'status': 'error', 'message': 'Бэкап не найден'}, status_code=404)
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

    for f in ['config/settings.json', 'data/users.json', 'data/proxies.json']:
        path = os.path.join('/opt/mtprotoserver', f)
        checks.append(f"{'✅' if os.path.exists(path) else '❌'} {f}")

    return JSONResponse({'status': 'ok', 'output': '\n'.join(checks)})

@app.get("/api/system/speedtest")
async def speed_test():
    try:
        import time
        # Download test
        start = time.time()
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{speed_download}',
                           'https://speed.cloudflare.com/__down?bytes=5000000'],
                          capture_output=True, text=True, timeout=30)
        download_speed = float(r.stdout) * 8 / 1000000 if r.stdout else 0
        download_time = time.time() - start

        # Upload test
        start = time.time()
        r2 = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{speed_upload}',
                            '-X', 'POST', '-d', 'x' * 1000000,
                            'https://speed.cloudflare.com/__up'],
                           capture_output=True, text=True, timeout=30)
        upload_speed = float(r2.stdout) * 8 / 1000000 if r2.stdout else 0
        upload_time = time.time() - start

        # Ping
        r3 = subprocess.run(['ping', '-c', '4', '-W', '2', '1.1.1.1'],
                           capture_output=True, text=True, timeout=10)
        ping = 'N/A'
        if r3.stdout:
            lines = r3.stdout.strip().split('\n')
            for line in lines:
                if 'avg' in line or 'rtt' in line:
                    ping = line.split('/')[4] if '/' in line else 'N/A'
                    break

        return JSONResponse({
            'status': 'ok',
            'download_mbps': round(download_speed, 2),
            'upload_mbps': round(upload_speed, 2),
            'ping_ms': ping,
            'download_time': round(download_time, 2),
            'upload_time': round(upload_time, 2)
        })
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/system/test-webhook")
async def test_webhook(request: Request):
    import requests as req
    form = await request.form()
    url = form.get('webhook_url', '')
    if not url:
        return JSONResponse({'status': 'error', 'message': 'URL обязателен'}, status_code=400)
    try:
        payload = {
            'text': '🟢 MTProtoSERVER: Тестовое уведомление работает!',
            'content': 'Это тестовое сообщение от MTProtoSERVER'
        }
        r = req.post(url, json=payload, timeout=10)
        return JSONResponse({'status': 'ok', 'response_code': r.status_code})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

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
        save_json(SETTINGS_FILE, settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/blacklist/remove")
async def remove_from_blacklist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    bl = settings.get('ip_blacklist', [])
    settings['ip_blacklist'] = [x for x in bl if x != ip]
    save_json(SETTINGS_FILE, settings)
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
        save_json(SETTINGS_FILE, settings)
    return JSONResponse({'status': 'ok'})

@app.post("/api/security/whitelist/remove")
async def remove_from_whitelist(request: Request):
    form = await request.form()
    ip = form.get('ip', '')
    settings = get_settings()
    wl = settings.get('ip_whitelist', [])
    settings['ip_whitelist'] = [x for x in wl if x != ip]
    save_json(SETTINGS_FILE, settings)
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
        return JSONResponse({'status': 'error', 'message': 'UFW недоступен'}, status_code=500)

@app.get("/api/security/firewall")
async def get_firewall_rules():
    try:
        r = subprocess.run(['ufw', 'status', 'numbered'], capture_output=True, text=True, timeout=10)
        rules = []
        if r.stdout:
            for line in r.stdout.strip().split('\n')[2:]:
                if line.strip():
                    rules.append(line.strip())
        return JSONResponse({'rules': rules})
    except:
        return JSONResponse({'rules': []})

@app.post("/api/security/ratelimit")
async def set_ratelimit(request: Request):
    form = await request.form()
    rate = int(form.get('rate', 100))
    settings = get_settings()
    settings['rate_limit'] = rate
    save_json(SETTINGS_FILE, settings)
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
