#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER — Скрипт обновления
# Скачивает последние файлы и пересобирает контейнеры
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/mtprotoserver"
REPO_URL="https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main"

E_OK="✅"
E_ERR="❌"
E_WARN="⚠️"
E_INFO="ℹ️"

log_ok()    { echo -e "${GREEN}${E_OK} $1${NC}"; }
log_err()   { echo -e "${RED}${E_ERR} $1${NC}"; }
log_warn()  { echo -e "${YELLOW}${E_WARN} $1${NC}"; }
log_info()  { echo -e "${BLUE}${E_INFO} $1${NC}"; }

if [ ! -d "$INSTALL_DIR" ]; then
    log_err "MTProtoSERVER не установлен в $INSTALL_DIR"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  MTProtoSERVER — Обновление${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Скачиваем файлы
log_info "Скачивание последних файлов..."

download_file() {
    local rel_path="$1"
    local dest="$INSTALL_DIR/$rel_path"
    mkdir -p "$(dirname "$dest")"
    if curl -fsSL --max-time 30 -o "$dest" "${REPO_URL}/${rel_path}" 2>/dev/null; then
        echo -e "  ${E_OK} $rel_path"
    else
        echo -e "  ${E_WARN} $rel_path (ошибка)"
    fi
}

download_file "webui/Dockerfile"
download_file "webui/requirements.txt"
download_file "webui/app.py"
download_file "webui/templates/base.html"
download_file "webui/templates/dashboard.html"
download_file "webui/templates/clients.html"
download_file "webui/templates/nodes.html"
download_file "webui/templates/stats.html"
download_file "webui/templates/settings.html"
download_file "webui/templates/security.html"
download_file "webui/templates/logs.html"
download_file "webui/templates/backup.html"
download_file "webui/templates/socks5.html"
download_file "webui/templates/http_proxy.html"
download_file "webui/static/css/style.css"
download_file "webui/static/js/app.js"
download_file "bot/Dockerfile"
download_file "bot/requirements.txt"
download_file "bot/bot.py"
download_file "scripts/auto-heal.sh"
download_file "scripts/auto-update.sh"
download_file "scripts/backup.sh"
download_file "scripts/health-check.sh"
download_file "scripts/monitor.sh"
download_file "scripts/rotate-domain.sh"
download_file "scripts/speedtest.sh"
download_file "scripts/add-proxy.sh"
download_file "scripts/remove-proxy.sh"
download_file "agent/Dockerfile"
download_file "agent/agent.py"
download_file "agent/requirements.txt"
download_file "agent/install.sh"
download_file "install.sh"
download_file "uninstall.sh"
download_file "README.md"

chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true

# Пересобираем
echo ""
log_info "Остановка контейнеров..."
cd "$INSTALL_DIR"
docker compose down 2>/dev/null || true

log_info "Удаление старых образов..."
docker rmi mtprotoserver-webui 2>/dev/null || true
docker rmi mtprotoserver-bot 2>/dev/null || true

log_info "Пересборка и запуск..."
docker compose pull
docker compose up -d --build --force-recreate

sleep 5

echo ""
if docker compose ps | grep -q "Up"; then
    log_ok "Обновление завершено! Все контейнеры работают."
else
    log_err "Ошибка запуска. Проверьте логи: docker compose logs"
fi

echo ""
log_info "Статус:"
docker compose ps
echo ""
