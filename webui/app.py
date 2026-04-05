from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json, os, subprocess, secrets as sec, psutil, io, qrcode, time, zipfile, tempfile
from datetime import datetime, timedelta

app = FastAPI(title="MTProtoSERVER")
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

def load_json(fp):
    try:
        with open(fp, 'r') as f: return json.load(f)
    except: return {}

def save_json(fp, data):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w') as f: json.dump(data, f, indent=4)

def init_files():
    if not os.path.exists(CLIENTS_FILE):
        save_json(CLIENTS_FILE, {"clients": [], "next_id": 1})
    if not os.path.exists(NODES_FILE):
        save_json(NODES_FILE, {"nodes": [], "next_id": 1})
    if not os.path.exists(AUTH_FILE):
        save_json(AUTH_FILE, {"token": "", "totp_secret": "", "totp_enabled": False})

init_files()

def get_settings():
    s = load_json(SETTINGS_FILE)
    # Get external IP from env var first, then try curl, then fallback
    env_ip = os.environ.get('PROXY_IP', '')
    if env_ip and env_ip != '0.0.0.0':
        s['proxy_ip'] = env_ip
    elif not s.get('proxy_ip') or s.get('proxy_ip') == '0.0.0.0':
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '5', 'ifconfig.me'], capture_output=True, text=True, timeout=10)
            if r.stdout.strip(): s['proxy_ip'] = r.stdout.strip()
        except: pass
    for k, v in {'proxy_port':443,'fake_domain':'cloudflare.com','webui_port':8080,'proxy_count':1,'bot_enabled':False,'bot_token':'','admin_chat_id':'','socks5_enabled':False,'socks5_port':1080,'socks5_user':'','socks5_pass':'','http_proxy_enabled':False,'http_proxy_port':3128,'http_proxy_user':'','http_proxy_pass':'','ad_tag':'','geoblock_countries':'','webhook_url':'','auto_heal':True,'auto_update':True,'backup_enabled':True,'backup_interval':'daily','monitor_interval':300,'geoblock':[],'ip_whitelist':[],'ip_blacklist':[],'rate_limit':100}.items():
        if k not in s: s[k] = v
    return s

def save_settings(d): save_json(SETTINGS_FILE, d)
def get_clients(): return load_json(CLIENTS_FILE)
def save_clients(d): save_json(CLIENTS_FILE, d)
def get_nodes(): return load_json(NODES_FILE)
def save_nodes(d): save_json(NODES_FILE, d)
def get_auth(): return load_json(AUTH_FILE)
def save_auth(d): save_json(AUTH_FILE, d)

def proxy_link(ip, port, secret): return f"tg://proxy?server={ip}&port={port}&secret={secret}"

def compose(args, timeout=60):
    try:
        r = subprocess.run(['docker','compose']+args, capture_output=True, text=True, cwd=HOST_DIR, timeout=timeout)
        return r.stdout if r.returncode == 0 else r.stderr
    except Exception as e: return str(e)

def docker_ps():
    try:
        r = subprocess.run(['docker','ps','-a','--format','{{.Names}}|{{.Status}}|{{.Ports}}'], capture_output=True, text=True, timeout=10)
        cs = []
        for l in r.stdout.strip().split('\n'):
            p = l.split('|')
            if len(p) >= 3: cs.append({'name':p[0],'status':p[1],'ports':p[2]})
        return cs
    except: return []

def sys_info():
    try:
        m = psutil.virtual_memory(); d = psutil.disk_usage('/')
        return {'cpu_percent':psutil.cpu_percent(),'memory_percent':m.percent,'memory_total_gb':round(m.total/(1024**3),1),'memory_used_gb':round(m.used/(1024**3),1),'disk_percent':d.percent,'disk_total_gb':round(d.total/(1024**3),1),'disk_used_gb':round(d.used/(1024**3),1)}
    except: return {'cpu_percent':0,'memory_percent':0,'memory_total_gb':0,'memory_used_gb':0,'disk_percent':0,'disk_total_gb':0,'disk_used_gb':0}

def fmt(b):
    if b==0: return "0 B"
    for u in ['B','KB','MB','GB','TB']:
        if b<1024: return f"{b:.1f} {u}"
        b/=1024
    return f"{b:.1f} PB"

def ctx(r):
    s = get_settings()
    return {'settings':s,'has_logo':os.path.exists(LOGO_FILE),'lang':'ru','now':datetime.now().strftime('%Y-%m-%d'),'request':r,'server_ip':s.get('proxy_ip','0.0.0.0')}

# AUTH
PROTECTED = ['/clients','/nodes','/stats','/settings','/security','/logs','/backup','/socks5','/http-proxy','/mtproto']

@app.middleware("http")
async def auth_mw(request, call_next):
    p = request.url.path
    if p=='/login' or p.startswith('/static') or p.startswith('/api/auth') or p=='/api/qr' or p=='/api/system/logo' or p.startswith('/api/public'):
        return await call_next(request)
    if p in PROTECTED or p=='/':
        a = get_auth()
        if a.get('token'):
            if request.cookies.get('auth_token','') != a['token']:
                return RedirectResponse(url='/login', status_code=302)
    return await call_next(request)
    if p in PROTECTED or p=='/':
        a = get_auth()
        if a.get('token'):
            if request.cookies.get('auth_token','') != a['token']:
                return RedirectResponse(url='/login', status_code=302)
    return await call_next(request)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {'request':request})

@app.post("/api/auth/login")
async def api_login(request: Request):
    form = await request.form()
    pw = form.get('password','')
    a = get_auth()
    if not a.get('token'): return JSONResponse({'status':'error','message':'Пароль не установлен'})
    if pw == a['token']:
        r = JSONResponse({'status':'ok'})
        r.set_cookie('auth_token', pw, httponly=True, max_age=86400*30)
        return r
    return JSONResponse({'status':'error','message':'Неверный пароль'}, status_code=401)

@app.post("/api/auth/logout")
async def api_logout():
    r = JSONResponse({'status':'ok'}); r.delete_cookie('auth_token'); return r

# PAGES
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    c = ctx(request)
    nd = get_nodes()
    ns = nd.get('nodes',[])
    # Use proxies.json for MTProto proxy count
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    proxies = pd.get('proxies', [])
    proxy_count = len(proxies)
    active_proxies = len([p for p in proxies if p.get('enabled', True)])
    # Also count clients
    cd = get_clients()
    cl = cd.get('clients',[])
    c.update({
        'clients':cl, 'nodes':ns,
        'clients_count': len(cl),
        'active_clients': len([x for x in cl if x.get('enabled',True)]),
        'proxy_count': proxy_count,
        'active_proxies': active_proxies,
        'nodes_count':len(ns),
        'total_rx': fmt(sum(x.get('rx_bytes',0) for x in cl)),
        'total_tx': fmt(sum(x.get('tx_bytes',0) for x in cl)),
        'system':sys_info(),
        'containers':docker_ps()
    })
    return templates.TemplateResponse("dashboard.html", c)

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    c = ctx(request); c.update({'clients':get_clients().get('clients',[]),'nodes':get_nodes().get('nodes',[])}); return templates.TemplateResponse("clients.html", c)

@app.get("/nodes", response_class=HTMLResponse)
async def nodes_page(request: Request):
    c = ctx(request); c.update({'nodes':get_nodes().get('nodes',[])}); return templates.TemplateResponse("nodes.html", c)

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    c = ctx(request)
    # Get proxies from proxies.json
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    proxies = pd.get('proxies', [])
    # Also get clients
    cd = get_clients()
    clients = cd.get('clients', [])
    # Merge both
    all_items = []
    for p in proxies:
        all_items.append({
            'label': p.get('label', ''),
            'port': p.get('port', 0),
            'domain': p.get('domain', ''),
            'enabled': p.get('enabled', True),
            'type': 'MTProto',
            'rx_bytes': p.get('traffic_in', 0),
            'tx_bytes': p.get('traffic_out', 0),
            'unique_ips': p.get('connections', 0),
            'created_at': p.get('created_at', '')
        })
    for cl in clients:
        exists = any(x['label'] == cl.get('label') for x in all_items)
        if not exists:
            all_items.append({
                'label': cl.get('label', ''),
                'port': cl.get('port', 0),
                'domain': cl.get('domain', ''),
                'enabled': cl.get('enabled', True),
                'type': 'Клиент',
                'rx_bytes': cl.get('rx_bytes', 0),
                'tx_bytes': cl.get('tx_bytes', 0),
                'unique_ips': cl.get('unique_ips', 0),
                'created_at': cl.get('created_at', '')
            })
    c.update({'clients': all_items, 'system': sys_info()})
    return templates.TemplateResponse("stats.html", c)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    c = ctx(request); c.update({'auth':get_auth()}); return templates.TemplateResponse("settings.html", c)

@app.get("/security", response_class=HTMLResponse)
async def security_page(request: Request): return templates.TemplateResponse("security.html", ctx(request))

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request): return templates.TemplateResponse("logs.html", ctx(request))

@app.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request): return templates.TemplateResponse("backup.html", ctx(request))

@app.get("/socks5", response_class=HTMLResponse)
async def socks5_page(request: Request): return templates.TemplateResponse("socks5.html", ctx(request))

@app.get("/http-proxy", response_class=HTMLResponse)
async def http_proxy_page(request: Request): return templates.TemplateResponse("http_proxy.html", ctx(request))

@app.get("/mtproto", response_class=HTMLResponse)
async def mtproto_page(request: Request): return templates.TemplateResponse("mtproto.html", ctx(request))

# CLIENTS API
@app.post("/api/clients/add")
async def add_client(request: Request):
    form = await request.form()
    label = form.get('label','client'); nid = int(form.get('node_id',0) or 0)
    tlg = float(form.get('traffic_limit_gb',0) or 0); dl = int(form.get('device_limit',0) or 0)
    ed = int(form.get('expiry_days',0) or 0)
    s = get_settings(); cd = get_clients(); cl = cd.get('clients',[]); nid2 = cd.get('next_id',1)
    dom = form.get('domain', s.get('fake_domain','cloudflare.com'))
    secret = f"ee{sec.token_hex(14)}{dom.encode().hex()}"; port = 443 + nid2
    exp = (datetime.now()+timedelta(days=ed)).strftime('%Y-%m-%d') if ed>0 else ''
    cl.append({'id':nid2,'label':label,'node_id':nid,'port':port,'domain':dom,'secret':secret,'enabled':True,'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'traffic_limit_gb':tlg,'device_limit':dl,'expiry_date':exp,'auto_reset':form.get('auto_reset','never'),'rx_bytes':0,'tx_bytes':0,'unique_ips':0,'connections':0,'history':[]})
    cd['clients']=cl; cd['next_id']=nid2+1; save_clients(cd)
    try: subprocess.run(['ufw','allow',str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    return JSONResponse({'status':'ok','secret':secret,'link':proxy_link(s.get('proxy_ip','0.0.0.0'),port,secret),'port':port})

@app.post("/api/clients/{cid}/toggle")
async def toggle_client(cid:int):
    cd=get_clients()
    for c in cd.get('clients',[]):
        if c['id']==cid: c['enabled']=not c.get('enabled',True); break
    save_clients(cd); return JSONResponse({'status':'ok'})

@app.post("/api/clients/{cid}/delete")
async def delete_client(cid:int):
    cd=get_clients(); cd['clients']=[c for c in cd.get('clients',[]) if c['id']!=cid]; save_clients(cd); return JSONResponse({'status':'ok'})

@app.post("/api/clients/{cid}/rotate")
async def rotate_client(cid:int):
    cd=get_clients(); s=get_settings()
    for c in cd.get('clients',[]):
        if c['id']==cid: c['secret']=f"ee{sec.token_hex(14)}{c.get('domain','cloudflare.com').encode().hex()}"; break
    save_clients(cd); return JSONResponse({'status':'ok','secret':c['secret'],'link':proxy_link(s.get('proxy_ip','0.0.0.0'),c['port'],c['secret'])})

@app.post("/api/clients/{cid}/reset-traffic")
async def reset_traffic(cid:int):
    cd=get_clients()
    for c in cd.get('clients',[]):
        if c['id']==cid: c['rx_bytes']=0; c['tx_bytes']=0; break
    save_clients(cd); return JSONResponse({'status':'ok'})

@app.get("/api/clients/{cid}/history")
async def get_history(cid:int):
    cd=get_clients()
    for c in cd.get('clients',[]):
        if c['id']==cid: return JSONResponse({'history':c.get('history',[])})
    return JSONResponse({'history':[]})

# NODES API
@app.post("/api/nodes/add")
async def add_node(request: Request):
    form=await request.form(); nd=get_nodes(); ns=nd.get('nodes',[]); nid=nd.get('next_id',1)
    ns.append({'id':nid,'name':form.get('name','node'),'ip':form.get('ip',''),'port':int(form.get('port',9876) or 9876),'country':form.get('country','🌍'),'token':form.get('token',''),'auth_type':form.get('auth_type','token'),'ssh_user':form.get('ssh_user',''),'ssh_pass':form.get('ssh_pass',''),'ssh_key':form.get('ssh_key',''),'enabled':True,'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'last_ping':'','status':'unknown'})
    nd['nodes']=ns; nd['next_id']=nid+1; save_nodes(nd); return JSONResponse({'status':'ok'})

@app.post("/api/nodes/{nid}/toggle")
async def toggle_node(nid:int):
    nd=get_nodes()
    for n in nd.get('nodes',[]):
        if n['id']==nid: n['enabled']=not n.get('enabled',True); break
    save_nodes(nd); return JSONResponse({'status':'ok'})

@app.post("/api/nodes/{nid}/delete")
async def delete_node(nid:int):
    nd=get_nodes(); nd['nodes']=[n for n in nd.get('nodes',[]) if n['id']!=nid]; save_nodes(nd); return JSONResponse({'status':'ok'})

@app.post("/api/nodes/{nid}/ping")
async def ping_node(nid:int):
    import requests as rq
    nd=get_nodes()
    for n in nd.get('nodes',[]):
        if n['id']==nid:
            try:
                r=rq.get(f"http://{n['ip']}:{n['port']}/health",timeout=5)
                n['status']='online' if r.status_code==200 else 'offline'
            except: n['status']='offline'
            n['last_ping']=datetime.now().strftime('%H:%M:%S'); save_nodes(nd)
            return JSONResponse({'status':'ok','node_status':n['status'],'last_ping':n['last_ping']})
    return JSONResponse({'status':'error','message':'Нода не найдена'}, status_code=404)

@app.post("/api/nodes/{nid}/sync")
async def sync_node(nid:int):
    import requests as rq
    nd=get_nodes(); cd=get_clients()
    for n in nd.get('nodes',[]):
        if n['id']==nid:
            try:
                r=rq.get(f"http://{n['ip']}:{n['port']}/clients",headers={'x-token':n['token']},timeout=10)
                remote=r.json().get('clients',[]); local=cd.get('clients',[])
                for rc in remote:
                    found=False
                    for lc in local:
                        if lc['label']==rc.get('label',''):
                            lc.update({'rx_bytes':rc.get('rx_bytes',0),'tx_bytes':rc.get('tx_bytes',0),'unique_ips':rc.get('unique_ips',0),'status':rc.get('status','unknown')}); found=True; break
                    if not found: local.append(rc)
                cd['clients']=local; save_clients(cd)
                return JSONResponse({'status':'ok','synced':len(remote)})
            except Exception as e: return JSONResponse({'status':'error','message':str(e)}, status_code=500)
    return JSONResponse({'status':'error','message':'Нода не найдена'}, status_code=404)

# PROXY MANAGEMENT
@app.post("/api/proxies/socks5/create")
async def create_socks5(request: Request):
    form=await request.form(); port=int(form.get('port',1080) or 1080); user=form.get('user',''); pw=form.get('password','')
    s=get_settings(); s['socks5_enabled']=True; s['socks5_port']=port; s['socks5_user']=user or 'без логина'; s['socks5_pass']=pw or 'без пароля'; save_settings(s)
    os.makedirs(f"{HOST_DIR}/config", exist_ok=True)
    if user and pw:
        with open(f"{HOST_DIR}/config/socks5.conf",'w') as f: f.write(f"logoutput: stderr\ninternal: 0.0.0.0 port = 1080\nexternal: eth0\nclientmethod: none\nsocksmethod: username\nuser.privileged: root\nuser.notprivileged: sockd\nuser.libwrap: nobody\nclient pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 }}\nsocks pass {{ from: 0.0.0.0/0 to: 0.0.0.0/0 user: {user} password: {pw} }}\n")
    else:
        with open(f"{HOST_DIR}/config/socks5.conf",'w') as f: f.write("logoutput: stderr\ninternal: 0.0.0.0 port = 1080\nexternal: eth0\nclientmethod: none\nsocksmethod: none\nuser.privileged: root\nuser.notprivileged: sockd\nuser.libwrap: nobody\nclient pass { from: 0.0.0.0/0 to: 0.0.0.0/0 }\nsocks pass { from: 0.0.0.0/0 to: 0.0.0.0/0 }\n")
    try: subprocess.run(['ufw','allow',str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    try:
        subprocess.run(['docker','rm','-f','mtproto-socks5'], capture_output=True, timeout=10)
        subprocess.run(['docker','run','-d','--name','mtproto-socks5','--restart','unless-stopped','-p',f'{port}:1080','-v',f'{HOST_DIR}/config/socks5.conf:/etc/sockd.conf:ro','--cap-add','NET_ADMIN','--network','mtprotoserver_mtproto-net','vimagick/dante'], capture_output=True, timeout=30)
    except: pass
    return JSONResponse({'status':'ok','port':port,'user':user,'password':pw,'no_auth':not user and not pw})

@app.post("/api/proxies/http/create")
async def create_http(request: Request):
    form=await request.form(); port=int(form.get('port',3128) or 3128); user=form.get('user',''); pw=form.get('password','')
    s=get_settings(); s['http_proxy_enabled']=True; s['http_proxy_port']=port; s['http_proxy_user']=user or 'без логина'; s['http_proxy_pass']=pw or 'без пароля'; save_settings(s)
    os.makedirs(f"{HOST_DIR}/config", exist_ok=True)
    if user and pw:
        with open(f"{HOST_DIR}/config/squid.conf",'w') as f: f.write("http_port 3128\ncache_dir ufs /var/spool/squid 100 16 256\ncoredump_dir /var/spool/squid\nhttp_access allow all\n")
    else:
        with open(f"{HOST_DIR}/config/squid.conf",'w') as f: f.write("http_port 3128\ncache_dir ufs /var/spool/squid 100 16 256\ncoredump_dir /var/spool/squid\nhttp_access allow all\n")
    try: subprocess.run(['ufw','allow',str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    try:
        subprocess.run(['docker','rm','-f','mtproto-http-proxy'], capture_output=True, timeout=10)
        subprocess.run(['docker','run','-d','--name','mtproto-http-proxy','--restart','unless-stopped','-p',f'{port}:3128','-v',f'{HOST_DIR}/config/squid.conf:/etc/squid/squid.conf:ro','--network','mtprotoserver_mtproto-net','sameersbn/squid:latest'], capture_output=True, timeout=30)
    except: pass
    return JSONResponse({'status':'ok','port':port,'user':user or 'без логина','password':pw or 'без пароля'})

@app.post("/api/proxies/socks5/delete")
async def delete_socks5():
    s=get_settings(); s['socks5_enabled']=False; save_settings(s)
    try: subprocess.run(['docker','rm','-f','mtproto-socks5'], capture_output=True, timeout=10)
    except: pass
    return JSONResponse({'status':'ok'})

@app.post("/api/proxies/http/delete")
async def delete_http():
    s=get_settings(); s['http_proxy_enabled']=False; save_settings(s)
    try: subprocess.run(['docker','rm','-f','mtproto-http-proxy'], capture_output=True, timeout=10)
    except: pass
    return JSONResponse({'status':'ok'})

# SYSTEM API
@app.post("/api/system/restart")
async def restart_system(): return JSONResponse({'status':'ok','message':compose(['restart'])})

@app.post("/api/system/restart-container")
async def restart_container(request: Request):
    form=await request.form(); name=form.get('name','')
    if name: return JSONResponse({'status':'ok','message':compose(['restart',name])})
    return JSONResponse({'status':'error'}, status_code=400)

@app.get("/api/system/logs")
async def get_logs(lines:int=100):
    # Try docker compose first, fallback to docker logs
    try:
        r = subprocess.run(['docker','compose','logs','--tail',str(lines)], capture_output=True, text=True, cwd=HOST_DIR, timeout=30)
        if r.returncode == 0: return JSONResponse({'status':'ok','logs':r.stdout})
    except: pass
    # Fallback: get logs from all containers
    try:
        r = subprocess.run(['docker','ps','--format','{{.Names}}'], capture_output=True, text=True, timeout=10)
        logs = ''
        for name in r.stdout.strip().split('\n'):
            if name:
                r2 = subprocess.run(['docker','logs','--tail',str(lines),name], capture_output=True, text=True, timeout=10)
                logs += f"\n=== {name} ===\n{r2.stdout}\n{r2.stderr}\n"
        return JSONResponse({'status':'ok','logs':logs})
    except Exception as e:
        return JSONResponse({'status':'error','message':str(e)}, status_code=500)

@app.post("/api/system/backup")
async def create_backup():
    os.makedirs(BACKUPS_DIR, exist_ok=True); ts=datetime.now().strftime('%Y%m%d_%H%M%S'); fn=f'backup_{ts}.tar.gz'; fp=os.path.join(BACKUPS_DIR,fn)
    try:
        subprocess.run(['tar','-czf',fp,'-C',HOST_DIR,'config','data','docker-compose.yml'], capture_output=True, timeout=30)
        sz=os.path.getsize(fp); return JSONResponse({'status':'ok','filename':fn,'size':f"{sz/1024:.1f} KB" if sz<1024*1024 else f"{sz/(1024*1024):.1f} MB"})
    except Exception as e: return JSONResponse({'status':'error','message':str(e)}, status_code=500)

@app.get("/api/system/backups")
async def list_backups():
    bs=[]
    if os.path.exists(BACKUPS_DIR):
        for f in sorted(os.listdir(BACKUPS_DIR), reverse=True):
            if f.endswith('.tar.gz'):
                sz=os.path.getsize(os.path.join(BACKUPS_DIR,f)); bs.append({'name':f,'size':f"{sz/1024:.1f} KB" if sz<1024*1024 else f"{sz/(1024*1024):.1f} MB"})
    return JSONResponse({'backups':bs})

@app.post("/api/system/restore")
async def restore_backup(request: Request):
    form=await request.form(); fp=os.path.join(BACKUPS_DIR,form.get('name',''))
    if not os.path.exists(fp): return JSONResponse({'status':'error','message':'Не найден'}, status_code=404)
    try: subprocess.run(['tar','-xzf',fp,'-C',HOST_DIR], capture_output=True, timeout=30); return JSONResponse({'status':'ok'})
    except Exception as e: return JSONResponse({'status':'error','message':str(e)}, status_code=500)

@app.post("/api/system/delete-backup")
async def delete_backup(request: Request):
    fp=os.path.join(BACKUPS_DIR,(await request.form()).get('name',''))
    if os.path.exists(fp): os.remove(fp)
    return JSONResponse({'status':'ok'})

@app.get("/api/system/health")
async def health_check():
    checks=[]
    # Docker check via socket
    try:
        r=subprocess.run(['docker','ps','--format','{{.Names}} {{.Status}}'], capture_output=True, text=True, timeout=10)
        if r.returncode==0:
            checks.append("✅ Docker: работает")
            if r.stdout.strip():
                checks.append("✅ Контейнеры:")
                for l in r.stdout.strip().split('\n'): checks.append(f"   {l}")
            else: checks.append("⚠️ Контейнеры не запущены")
        else:
            checks.append("❌ Docker: не доступен")
    except: checks.append("❌ Docker: не доступен")
    d=psutil.disk_usage('/'); m=psutil.virtual_memory()
    checks.append(f"{'✅' if d.percent<90 else '⚠️'} Диск: {d.percent}% использовано")
    checks.append(f"{'✅' if m.percent<90 else '⚠️'} RAM: {m.percent}% использовано")
    for f in ['config/settings.json','data/clients.json','data/nodes.json']:
        fp = os.path.join('/app',f)
        if not os.path.exists(fp):
            # Create if missing
            if 'clients.json' in f: save_json(fp, {"clients":[],"next_id":1})
            elif 'nodes.json' in f: save_json(fp, {"nodes":[],"next_id":1})
        checks.append(f"{'✅' if os.path.exists(fp) else '❌'} {f}")
    return JSONResponse({'status':'ok','output':'\n'.join(checks)})

@app.get("/api/system/speedtest")
async def speed_test():
    import requests as rq
    try:
        start=time.time(); r=rq.get('https://speed.cloudflare.com/__down?bytes=5000000',timeout=30)
        dl=len(r.content)/(time.time()-start)*8/1000000
        start2=time.time(); rq.post('https://speed.cloudflare.com/__up',data=b'x'*1000000,timeout=30)
        ul=1000000/(time.time()-start2)*8/1000000
        start3=time.time(); rq.get('https://1.1.1.1',timeout=5); ping=round((time.time()-start3)*1000,1)
        return JSONResponse({'status':'ok','download_mbps':round(dl,2),'upload_mbps':round(ul,2),'ping_ms':ping})
    except Exception as e: return JSONResponse({'status':'error','message':str(e)}, status_code=500)

@app.post("/api/system/update")
async def update_system():
    msg=compose(['pull']); msg+=compose(['up','-d','--build','--force-recreate'])
    return JSONResponse({'status':'ok','message':msg})

@app.post("/api/system/uninstall")
async def uninstall_system():
    compose(['down','--rmi','all','--volumes','--remove-orphans'])
    return JSONResponse({'status':'ok'})

@app.post("/api/system/set-adtag")
async def set_adtag(request: Request):
    form=await request.form(); s=get_settings(); s['ad_tag']=form.get('ad_tag',''); save_settings(s); return JSONResponse({'status':'ok'})

@app.post("/api/system/rotate-domain")
async def rotate_domain(request: Request):
    form=await request.form(); s=get_settings(); s['fake_domain']=form.get('domain','cloudflare.com'); save_settings(s); return JSONResponse({'status':'ok','domain':s['fake_domain']})

@app.post("/api/system/test-webhook")
async def test_webhook(request: Request):
    import requests as rq
    form=await request.form(); url=form.get('webhook_url','')
    if not url: return JSONResponse({'status':'error'}, status_code=400)
    try:
        r=rq.post(url,json={'text':'🟢 MTProtoSERVER: Тест работает!'},timeout=10)
        return JSONResponse({'status':'ok','response_code':r.status_code})
    except Exception as e: return JSONResponse({'status':'error','message':str(e)}, status_code=500)

@app.post("/api/system/upload-logo")
async def upload_logo(request: Request):
    form=await request.form(); f=form.get('logo')
    if f and hasattr(f,'read'):
        with open(LOGO_FILE,'wb') as fw: fw.write(await f.read())
        return JSONResponse({'status':'ok'})
    return JSONResponse({'status':'error'}, status_code=400)

@app.get("/api/system/logo")
async def get_logo():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE,'rb') as f: return StreamingResponse(io.BytesIO(f.read()), media_type="image/png")
    raise HTTPException(status_code=404)

@app.get("/api/qr")
async def gen_qr(text:str):
    qr=qrcode.QRCode(version=1,box_size=10,border=5); qr.add_data(text); qr.make(fit=True)
    img=qr.make_image(fill_color="black",back_color="white"); buf=io.BytesIO(); img.save(buf,format='PNG'); buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/api/status")
async def api_status():
    s=get_settings(); cd=get_clients(); nd=get_nodes(); cl=cd.get('clients',[]); ns=nd.get('nodes',[])
    return JSONResponse({'proxy_ip':s.get('proxy_ip'),'clients_count':len(cl),'active_clients':len([c for c in cl if c.get('enabled')]),'nodes_count':len(ns),'system':sys_info(),'containers':docker_ps()})

@app.get("/api/metrics")
async def api_metrics():
    cd=get_clients(); cl=cd.get('clients',[])
    m=f"# HELP mtproto_clients_total Total clients\n# TYPE mtproto_clients_total gauge\nmtproto_clients_total {len(cl)}\n# HELP mtproto_clients_active Active clients\n# TYPE mtproto_clients_active gauge\nmtproto_clients_active {len([c for c in cl if c.get('enabled')])}\n"
    for c in cl: m+=f"# HELP mtproto_rx RX for {c['label']}\n# TYPE mtproto_rx counter\nmtproto_rx{{client=\"{c['label']}\"}} {c.get('rx_bytes',0)}\n"
    return HTMLResponse(content=m)

# MTProto secret generation
@app.get("/api/mtproto/generate-secret")
async def generate_secret():
    dom = get_settings().get('fake_domain','cloudflare.com')
    secret = f"ee{sec.token_hex(14)}{dom.encode().hex()}"
    return JSONResponse({'status':'ok','secret':secret,'domain':dom})

# Create new MTProto proxy instance
@app.post("/api/mtproto/create")
async def create_mtproto(request: Request):
    form = await request.form()
    label = form.get('label', 'proxy')
    port = int(form.get('port', 443) or 443)
    domain = form.get('domain', get_settings().get('fake_domain', 'cloudflare.com'))
    secret = form.get('secret', '')
    if not secret:
        secret = f"ee{sec.token_hex(14)}{domain.encode().hex()}"
    s = get_settings()
    # Open port
    try: subprocess.run(['ufw', 'allow', str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    # Save to proxies.json FIRST (single source of truth)
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    pl = pd.get('proxies', [])
    p_next_id = pd.get('next_id', 1)
    pl.append({
        'id': p_next_id, 'label': label, 'port': port, 'domain': domain,
        'secret': secret, 'enabled': True, 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'connections': 0, 'traffic_in': 0, 'traffic_out': 0
    })
    pd['proxies'] = pl
    pd['next_id'] = p_next_id + 1
    save_json(os.path.join(DATA_DIR, 'proxies.json'), pd)
    # Update proxy count
    s['proxy_count'] = s.get('proxy_count', 1) + 1
    save_settings(s)
    # Try to create container (may fail inside container, but proxy is already saved)
    container_name = f'mtproto-proxy-{label}'
    try:
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, timeout=10)
        subprocess.run(['docker', 'run', '-d', '--name', container_name, '--restart', 'unless-stopped',
                       '-p', f'{port}:{port}', '--network', 'mtprotoserver_mtproto-net',
                       'nineseconds/mtg:2', 'simple-run', '-n', '1.1.1.1', '-i', 'prefer-ipv4',
                       f'0.0.0.0:{port}', secret], capture_output=True, timeout=30)
    except: pass
    return JSONResponse({'status': 'ok', 'label': label, 'port': port, 'secret': secret,
                        'link': proxy_link(s.get('proxy_ip', '0.0.0.0'), port, secret)})

# Create new MTProto proxy instance
@app.post("/api/mtproto/create")
async def create_mtproto(request: Request):
    form = await request.form()
    label = form.get('label', 'proxy')
    port = int(form.get('port', 443) or 443)
    domain = form.get('domain', get_settings().get('fake_domain', 'cloudflare.com'))
    secret = form.get('secret', '')
    if not secret:
        secret = f"ee{sec.token_hex(14)}{domain.encode().hex()}"
    s = get_settings()
    # Open port
    try: subprocess.run(['ufw', 'allow', str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    # Save to proxies.json FIRST (single source of truth)
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    pl = pd.get('proxies', [])
    p_next_id = pd.get('next_id', 1)
    pl.append({
        'id': p_next_id, 'label': label, 'port': port, 'domain': domain,
        'secret': secret, 'enabled': True, 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'connections': 0, 'traffic_in': 0, 'traffic_out': 0
    })
    pd['proxies'] = pl
    pd['next_id'] = p_next_id + 1
    save_json(os.path.join(DATA_DIR, 'proxies.json'), pd)
    # Update proxy count
    s['proxy_count'] = s.get('proxy_count', 1) + 1
    save_settings(s)
    # Try to create container (may fail inside container, but proxy is already saved)
    container_name = f'mtproto-proxy-{label}'
    try:
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, timeout=10)
        subprocess.run(['docker', 'run', '-d', '--name', container_name, '--restart', 'unless-stopped',
                       '-p', f'{port}:{port}', '--network', 'mtprotoserver_mtproto-net',
                       'nineseconds/mtg:2', 'simple-run', '-n', '1.1.1.1', '-i', 'prefer-ipv4',
                       f'0.0.0.0:{port}', secret], capture_output=True, timeout=30)
    except: pass
    return JSONResponse({'status': 'ok', 'label': label, 'port': port, 'secret': secret,
                        'link': proxy_link(s.get('proxy_ip', '0.0.0.0'), port, secret)})

@app.post("/api/mtproto/{label}/delete")
async def delete_mtproto(label: str):
    from urllib.parse import unquote
    label = unquote(label)
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    before = len(pd.get('proxies', []))
    pd['proxies'] = [p for p in pd.get('proxies', []) if p.get('label') != label]
    after = len(pd.get('proxies', []))
    save_json(os.path.join(DATA_DIR, 'proxies.json'), pd)
    # Update settings
    s = get_settings()
    s['proxy_count'] = after
    save_settings(s)
    # Try to remove container
    try: subprocess.run(['docker', 'rm', '-f', f'mtproto-proxy-{label}'], capture_output=True, timeout=10)
    except: pass
    return JSONResponse({'status': 'ok', 'deleted': before > after, 'label': label})

@app.post("/api/mtproto/{label}/update")
async def update_mtproto(label: str, request: Request):
    form = await request.form()
    new_port = int(form.get('port', 0) or 0)
    new_domain = form.get('domain', '')
    new_secret = form.get('secret', '')
    new_label = form.get('new_label', label)
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    proxy = None
    for p in pd.get('proxies', []):
        if p.get('label') == label:
            proxy = p; break
    if not proxy:
        return JSONResponse({'status': 'error', 'message': 'Прокси не найден'}, status_code=404)
    port = new_port or proxy.get('port', 443)
    domain = new_domain or proxy.get('domain', 'cloudflare.com')
    if new_secret:
        secret = new_secret
    elif new_domain and new_domain != proxy.get('domain'):
        secret = f"ee{sec.token_hex(14)}{domain.encode().hex()}"
    else:
        secret = proxy.get('secret', '')
    try: subprocess.run(['docker', 'rm', '-f', f'mtproto-proxy-{label}'], capture_output=True, timeout=10)
    except: pass
    try: subprocess.run(['ufw', 'allow', str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    container_name = f'mtproto-proxy-{new_label}'
    try:
        subprocess.run(['docker', 'run', '-d', '--name', container_name, '--restart', 'unless-stopped',
                       '-p', f'{port}:{port}', '--network', 'mtprotoserver_mtproto-net',
                       'nineseconds/mtg:2', 'simple-run', '-n', '1.1.1.1', '-i', 'prefer-ipv4',
                       f'0.0.0.0:{port}', secret], capture_output=True, timeout=30)
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)
    for p in pd.get('proxies', []):
        if p.get('label') == label:
            p['label'] = new_label; p['port'] = port; p['domain'] = domain; p['secret'] = secret; break
    save_json(os.path.join(DATA_DIR, 'proxies.json'), pd)
    return JSONResponse({'status': 'ok', 'label': new_label, 'port': port, 'secret': secret,
                        'link': proxy_link(ip, port, secret)})

@app.get("/api/mtproto/list")
async def list_mtproto():
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    proxies = []
    for p in pd.get('proxies', []):
        proxies.append({
            'label': p.get('label', ''), 'port': p.get('port', 0), 'domain': p.get('domain', ''),
            'secret': p.get('secret', ''), 'enabled': p.get('enabled', True),
            'link': proxy_link(ip, p.get('port', 0), p.get('secret', ''))
        })
    return JSONResponse({'proxies': proxies})

@app.post("/api/mtproto/{label}/update")
async def update_mtproto(label: str, request: Request):
    from urllib.parse import unquote
    label = unquote(label)
    form = await request.form()
    new_port = int(form.get('port', 0) or 0)
    new_domain = form.get('domain', '')
    new_secret = form.get('secret', '')
    new_label = form.get('new_label', label)
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    proxy = None
    for p in pd.get('proxies', []):
        if p.get('label') == label:
            proxy = p; break
    if not proxy:
        return JSONResponse({'status': 'error', 'message': 'Прокси не найден'}, status_code=404)
    port = new_port or proxy.get('port', 443)
    domain = new_domain or proxy.get('domain', 'cloudflare.com')
    if new_secret:
        secret = new_secret
    elif new_domain and new_domain != proxy.get('domain'):
        secret = f"ee{sec.token_hex(14)}{domain.encode().hex()}"
    else:
        secret = proxy.get('secret', '')
    try: subprocess.run(['docker', 'rm', '-f', f'mtproto-proxy-{label}'], capture_output=True, timeout=10)
    except: pass
    try: subprocess.run(['ufw', 'allow', str(port)+'/tcp'], capture_output=True, timeout=10)
    except: pass
    container_name = f'mtproto-proxy-{new_label}'
    try:
        subprocess.run(['docker', 'run', '-d', '--name', container_name, '--restart', 'unless-stopped',
                       '-p', f'{port}:{port}', '--network', 'mtprotoserver_mtproto-net',
                       'nineseconds/mtg:2', 'simple-run', '-n', '1.1.1.1', '-i', 'prefer-ipv4',
                       f'0.0.0.0:{port}', secret], capture_output=True, timeout=30)
    except: pass
    for p in pd.get('proxies', []):
        if p.get('label') == label:
            p['label'] = new_label; p['port'] = port; p['domain'] = domain; p['secret'] = secret; break
    save_json(os.path.join(DATA_DIR, 'proxies.json'), pd)
    return JSONResponse({'status': 'ok', 'label': new_label, 'port': port, 'secret': secret,
                        'link': proxy_link(ip, port, secret)})

# =================== PUBLIC API (no auth required) ===================

def get_all_mtproto():
    """Get MTProto proxies from proxies.json (single source of truth)"""
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    proxies = []
    pd = load_json(os.path.join(DATA_DIR, 'proxies.json'))
    for p in pd.get('proxies', []):
        if p.get('enabled', True):
            proxies.append({
                'label': p.get('label', ''),
                'port': p.get('port', 0),
                'domain': p.get('domain', ''),
                'secret': p.get('secret', ''),
                'link': proxy_link(ip, p.get('port', 0), p.get('secret', ''))
            })
    return proxies

@app.get("/api/public/proxies")
async def public_proxies():
    """Публичный API — все прокси сервера для вашего сайта"""
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    mtproto = get_all_mtproto()
    socks5 = {
        'enabled': s.get('socks5_enabled', False),
        'port': s.get('socks5_port', 0),
        'link': f"socks5://{ip}:{s.get('socks5_port', 0)}" if s.get('socks5_enabled') else ''
    }
    http = {
        'enabled': s.get('http_proxy_enabled', False),
        'port': s.get('http_proxy_port', 0),
        'link': f"http://{ip}:{s.get('http_proxy_port', 0)}" if s.get('http_proxy_enabled') else ''
    }
    return JSONResponse({
        'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'server_ip': ip,
        'mtproto': mtproto,
        'socks5': socks5,
        'http': http
    })

@app.get("/api/public/mtproto")
async def public_mtproto():
    """Публичный API — только MTProto прокси (массив ссылок)"""
    proxies = get_all_mtproto()
    return JSONResponse({'proxies': proxies, 'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')})

@app.get("/api/public/docs", response_class=HTMLResponse)
async def public_docs(request: Request):
    """Страница документации публичного API"""
    s = get_settings()
    ip = s.get('proxy_ip', '0.0.0.0')
    port = s.get('webui_port', 8080)
    base_url = f"http://{ip}:{port}"
    return templates.TemplateResponse("public_docs.html", {
        'request': request, 'base_url': base_url, 'server_ip': ip,
        'has_logo': os.path.exists(LOGO_FILE), 'lang': 'ru', 'now': datetime.now().strftime('%Y-%m-%d'),
        'settings': s
    })

# SECURITY API
@app.get("/api/security/ip-lists")
async def get_ip_lists():
    s=get_settings(); return JSONResponse({'blacklist':s.get('ip_blacklist',[]),'whitelist':s.get('ip_whitelist',[])})

@app.post("/api/security/blacklist/add")
async def add_bl(request: Request):
    form=await request.form(); ip=form.get('ip',''); s=get_settings(); bl=s.get('ip_blacklist',[])
    if ip not in bl: bl.append(ip); s['ip_blacklist']=bl; save_settings(s)
    return JSONResponse({'status':'ok'})

@app.post("/api/security/blacklist/remove")
async def rm_bl(request: Request):
    form=await request.form(); ip=form.get('ip',''); s=get_settings(); s['ip_blacklist']=[x for x in s.get('ip_blacklist',[]) if x!=ip]; save_settings(s)
    return JSONResponse({'status':'ok'})

@app.post("/api/security/whitelist/add")
async def add_wl(request: Request):
    form=await request.form(); ip=form.get('ip',''); s=get_settings(); wl=s.get('ip_whitelist',[])
    if ip not in wl: wl.append(ip); s['ip_whitelist']=wl; save_settings(s)
    return JSONResponse({'status':'ok'})

@app.post("/api/security/whitelist/remove")
async def rm_wl(request: Request):
    form=await request.form(); ip=form.get('ip',''); s=get_settings(); s['ip_whitelist']=[x for x in s.get('ip_whitelist',[]) if x!=ip]; save_settings(s)
    return JSONResponse({'status':'ok'})

@app.post("/api/security/firewall")
async def manage_fw(request: Request):
    form=await request.form(); port=form.get('port',''); action=form.get('action','allow')
    try:
        cmd='allow' if action=='allow' else 'deny'
        subprocess.run(['ufw',cmd,str(port)+'/tcp'], capture_output=True, timeout=10)
        return JSONResponse({'status':'ok'})
    except: return JSONResponse({'status':'error','message':'UFW недоступен'}, status_code=500)

@app.get("/api/security/firewall")
async def get_fw():
    try:
        r=subprocess.run(['ufw','status','numbered'], capture_output=True, text=True, timeout=10)
        rules=[l.strip() for l in r.stdout.strip().split('\n')[2:] if l.strip()] if r.stdout else []
        return JSONResponse({'rules':rules})
    except: return JSONResponse({'rules':[]})

@app.post("/api/security/ratelimit")
async def set_rl(request: Request):
    form=await request.form(); s=get_settings(); s['rate_limit']=int(form.get('rate',100)); save_settings(s)
    return JSONResponse({'status':'ok'})

@app.get("/api/security/export")
async def export_configs():
    zp=tempfile.mktemp(suffix='.zip')
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as zf:
        for root,dirs,files in os.walk(HOST_DIR):
            if 'backups' in root or '.git' in root: continue
            for f in files:
                fp=os.path.join(root,f); zf.write(fp,os.path.relpath(fp,HOST_DIR))
    def iterfile():
        with open(zp,'rb') as f: yield from f
        os.unlink(zp)
    return StreamingResponse(iterfile(), media_type='application/zip', headers={'Content-Disposition':'attachment; filename=mtprotoserver-configs.zip'})
