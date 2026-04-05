from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import json
import os
import subprocess
import psutil

app = FastAPI(title="MTProtoSERVER Web UI")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "/app/data"
CONFIG_DIR = "/app/config"
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

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

def save_users(users):
    save_json(USERS_FILE, users)

def get_proxy_link(secret=None):
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    port = s.get('proxy_port', 443)
    if secret:
        return f"tg://proxy?server={ip}&port={port}&secret={secret}"
    return f"tg://proxy?server={ip}&port={port}"

def get_proxy_stats():
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps'],
            capture_output=True, text=True, cwd='/opt/mtprotoserver'
        )
        return result.stdout
    except:
        return "Недоступно"

def get_system_info():
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_total': psutil.virtual_memory().total // (1024**3),
        'memory_used': psutil.virtual_memory().used // (1024**3),
        'disk_percent': psutil.disk_usage('/').percent,
        'disk_total': psutil.disk_usage('/').total // (1024**3),
        'disk_used': psutil.disk_usage('/').used // (1024**3),
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    settings = get_settings()
    users_data = get_users()
    system = get_system_info()
    users = users_data.get('users', [])
    active_users = len([u for u in users if u.get('enabled', True)])
    total_traffic = sum(u.get('traffic_in', 0) + u.get('traffic_out', 0) for u in users)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings,
        "users_count": len(users),
        "active_users": active_users,
        "total_traffic": total_traffic,
        "system": system,
        "proxy_link": get_proxy_link()
    })

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    users_data = get_users()
    users = users_data.get('users', [])
    settings = get_settings()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "settings": settings,
        "proxy_link": get_proxy_link()
    })

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    users_data = get_users()
    users = users_data.get('users', [])
    system = get_system_info()
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "users": users,
        "system": system
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
    proxy_status = get_proxy_stats()
    return templates.TemplateResponse("diagnostics.html", {
        "request": request,
        "system": system,
        "proxy_status": proxy_status
    })

@app.post("/api/users/add")
async def add_user(request: Request):
    form = await request.form()
    label = form.get('label', 'user')
    users_data = get_users()
    users = users_data.get('users', [])
    next_id = users_data.get('next_id', 1)

    import secrets
    new_secret = secrets.token_hex(16)

    new_user = {
        'id': next_id,
        'label': label,
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

    return JSONResponse({'status': 'ok', 'secret': new_secret, 'link': get_proxy_link(new_secret)})

@app.post("/api/users/{user_id}/toggle")
async def toggle_user(user_id: int):
    users_data = get_users()
    users = users_data.get('users', [])
    for u in users:
        if u['id'] == user_id:
            u['enabled'] = not u.get('enabled', True)
            break
    save_users(users_data)
    return JSONResponse({'status': 'ok'})

@app.post("/api/users/{user_id}/delete")
async def delete_user(user_id: int):
    users_data = get_users()
    users = users_data.get('users', [])
    users = [u for u in users if u['id'] != user_id]
    users_data['users'] = users
    save_users(users_data)
    return JSONResponse({'status': 'ok'})

@app.get("/api/status")
async def api_status():
    settings = get_settings()
    system = get_system_info()
    users_data = get_users()
    users = users_data.get('users', [])
    return JSONResponse({
        'proxy_ip': settings.get('proxy_ip'),
        'proxy_port': settings.get('proxy_port'),
        'fake_domain': settings.get('fake_domain'),
        'users_count': len(users),
        'active_users': len([u for u in users if u.get('enabled')]),
        'system': system
    })

@app.get("/api/metrics")
async def api_metrics():
    users_data = get_users()
    users = users_data.get('users', [])
    metrics = "# HELP mtproto_users_total Total users\n# TYPE mtproto_users_total gauge\n"
    metrics += f"mtproto_users_total {len(users)}\n"
    metrics += "# HELP mtproto_users_active Active users\n# TYPE mtproto_users_active gauge\n"
    metrics += f"mtproto_users_active {len([u for u in users if u.get('enabled')])}\n"
    for u in users:
        metrics += f"# HELP mtproto_user_traffic_in Traffic in for {u['label']}\n"
        metrics += f"# TYPE mtproto_user_traffic_in counter\n"
        metrics += f'mtproto_user_traffic_in{{user="{u["label"]}"}} {u.get("traffic_in", 0)}\n'
    return HTMLResponse(content=metrics)
