#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER - Полный установщик MTProto прокси
# Версия: 1.0.0
# Дата: 2026-04-05
# Поддержка: FakeTLS, Multi-User, Web UI, Telegram Bot
# ============================================================

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Эмодзи
E_OK="✅"
E_ERR="❌"
E_WARN="⚠️"
E_INFO="ℹ️"
E_STAR="⭐"
E_ARROW="➜"
E_KEY="🔑"
E_LOCK="🔒"
E_NET="🌐"
E_BOT="🤖"
E_SHIELD="🛡️"
E_CHART="📊"
E_GEAR="⚙️"
E_FILE="📁"
E_MAIL="📧"
E_PHONE="📱"

# Переменные
INSTALL_DIR="/opt/mtprotoserver"
PROXY_PORT=443
FAKE_DOMAIN=""
BOT_TOKEN=""
BOT_ENABLED="no"
ADMIN_CHAT_ID=""
PROXY_SECRET=""
SERVER_IP=""
WEBUI_PORT=8080

# ============================================================
# Утилиты
# ============================================================

log_ok()    { echo -e "${GREEN}${E_OK} $1${NC}"; }
log_err()   { echo -e "${RED}${E_ERR} $1${NC}"; }
log_warn()  { echo -e "${YELLOW}${E_WARN} $1${NC}"; }
log_info()  { echo -e "${BLUE}${E_INFO} $1${NC}"; }
log_cyan()  { echo -e "${CYAN}${E_ARROW} $1${NC}"; }
print_sep() { echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

print_header() {
    clear
    print_sep
    echo -e "${WHITE}${E_STAR}  MTProtoSERVER — Установщик MTProto Прокси${NC}"
    echo -e "${CYAN}   Версия 1.0.0 | 2026 | FakeTLS + Web UI + Bot${NC}"
    print_sep
    echo ""
}

print_step() {
    echo ""
    print_sep
    echo -e "${WHITE}${E_GEAR}  ШАГ $1: $2${NC}"
    print_sep
    echo ""
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_err "Запустите скрипт от root (sudo bash install.sh)"
        exit 1
    fi
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$ID"
        OS_VERSION="$VERSION_ID"
        log_ok "ОС определена: $OS_NAME $OS_VERSION"
    else
        log_warn "Не удалось определить ОС. Продолжаем..."
        OS_NAME="unknown"
    fi
}

get_server_ip() {
    SERVER_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || curl -s --max-time 5 ipinfo.io/ip 2>/dev/null || echo "0.0.0.0")
    if [ "$SERVER_IP" = "0.0.0.0" ]; then
        log_warn "Не удалось определить внешний IP"
        read -p "Введите внешний IP сервера: " SERVER_IP
    else
        log_ok "Внешний IP: $SERVER_IP"
    fi
}

generate_secret() {
    PROXY_SECRET=$(openssl rand -hex 16)
    log_ok "Секрет сгенерирован: ${E_KEY} $PROXY_SECRET"
}

generate_ee_secret() {
    local domain="$1"
    local domain_hex=$(echo -n "$domain" | xxd -p | tr -d '\n')
    local random_part=$(openssl rand -hex 14)
    PROXY_SECRET="ee${random_part}${domain_hex}"
    log_ok "FakeTLS секрет сгенерирован для домена: $domain"
}

# ============================================================
# ШАГ 1: Проверка системы
# ============================================================

step_system_check() {
    print_step "1" "Проверка системы"

    check_root
    check_os

    log_info "Проверка необходимых утилит..."

    local missing=()
    for cmd in curl openssl; do
        if ! command -v $cmd &>/dev/null; then
            missing+=($cmd)
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_warn "Установка недостающих утилит: ${missing[*]}"
        if command -v apt-get &>/dev/null; then
            apt-get update -qq && apt-get install -y -qq ${missing[@]} xxd
        elif command -v yum &>/dev/null; then
            yum install -y ${missing[@]} xxd
        elif command -v apk &>/dev/null; then
            apk add --no-cache ${missing[@]} xxd
        fi
    fi

    get_server_ip
    echo ""
    log_ok "Проверка системы завершена!"
    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 2: Установка Docker
# ============================================================

step_install_docker() {
    print_step "2" "Установка Docker"

    if command -v docker &>/dev/null; then
        log_ok "Docker уже установлен: $(docker --version)"
        if ! command -v docker compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
            log_warn "Docker Compose не найден, устанавливаем..."
        else
            log_ok "Docker Compose доступен"
            read -p "Нажмите Enter для продолжения..."
            return
        fi
    fi

    log_info "Установка Docker..."

    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || \
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS_NAME $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 2>/dev/null || true
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif command -v yum &>/dev/null; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null || true
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif command -v apk &>/dev/null; then
        apk add --no-cache docker docker-compose
        rc-update add docker boot
        service docker start
    else
        curl -fsSL https://get.docker.com | sh
    fi

    systemctl enable docker
    systemctl start docker

    if command -v docker &>/dev/null; then
        log_ok "Docker установлен: $(docker --version)"
        if docker compose version &>/dev/null 2>&1; then
            log_ok "Docker Compose: $(docker compose version)"
        fi
    else
        log_err "Не удалось установить Docker!"
        exit 1
    fi

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 3: Настройка прокси
# ============================================================

step_proxy_config() {
    print_step "3" "Настройка MTProto прокси"

    echo -e "${CYAN}${E_SHIELD}  FakeTLS — Маскировка под HTTPS трафик${NC}"
    echo -e "   Прокси будет работать на порту 443"
    echo -e "   Трафик маскируется под обычный HTTPS к выбранному домену"
    echo -e "   Для DPI это выглядит как посещение обычного сайта"
    echo ""

    # Выбор домена
    echo -e "${WHITE}Доступные домены для маскировки:${NC}"
    echo -e "  1) cloudflare.com  (рекомендуется)"
    echo -e "  2) 1c.ru"
    echo -e "  3) sberbank.ru"
    echo -e "  4) yandex.ru"
    echo -e "  5) mail.ru"
    echo -e "  6) vk.com"
    echo -e "  7) gosuslugi.ru"
    echo -e "  8) Ввести свой домен"
    echo ""

    read -p "Выберите домен [1-8] (по умолчанию 1): " domain_choice
    domain_choice=${domain_choice:-1}

    case $domain_choice in
        1) FAKE_DOMAIN="cloudflare.com" ;;
        2) FAKE_DOMAIN="1c.ru" ;;
        3) FAKE_DOMAIN="sberbank.ru" ;;
        4) FAKE_DOMAIN="yandex.ru" ;;
        5) FAKE_DOMAIN="mail.ru" ;;
        6) FAKE_DOMAIN="vk.com" ;;
        7) FAKE_DOMAIN="gosuslugi.ru" ;;
        8)
            read -p "Введите домен для маскировки: " FAKE_DOMAIN
            ;;
        *) FAKE_DOMAIN="cloudflare.com" ;;
    esac

    log_ok "Домен маскировки: ${E_NET} $FAKE_DOMAIN"
    echo ""

    # Порт прокси
    read -p "Порт прокси [443]: " port_input
    PROXY_PORT=${port_input:-443}
    log_ok "Порт прокси: $PROXY_PORT"
    echo ""

    # Порт Web UI
    read -p "Порт Web UI [8080]: " webui_input
    WEBUI_PORT=${webui_input:-8080}
    log_ok "Порт Web UI: $WEBUI_PORT"
    echo ""

    # Генерация секрета
    generate_ee_secret "$FAKE_DOMAIN"

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 4: Настройка Telegram бота
# ============================================================

step_bot_config() {
    print_step "4" "Настройка Telegram бота"

    echo -e "${CYAN}${E_BOT}  Telegram бот для управления прокси${NC}"
    echo -e "   Бот позволяет управлять прокси прямо из Telegram"
    echo -e "   Команды: /start, /adduser, /stats, /listusers и др."
    echo ""

    read -p "Установить Telegram бот? [y/n] (по умолчанию y): " bot_choice
    bot_choice=${bot_choice:-y}

    if [[ "$bot_choice" =~ ^[Yy]$ ]]; then
        BOT_ENABLED="yes"
        echo ""
        echo -e "${WHITE}Как получить токен бота:${NC}"
        echo -e "  1. Откройте @BotFather в Telegram"
        echo -e "  2. Отправьте /newbot"
        echo -e "  3. Введите имя и username бота"
        echo -e "  4. Скопируйте полученный токен"
        echo ""
        read -p "Введите токен бота: " BOT_TOKEN

        if [ -z "$BOT_TOKEN" ]; then
            log_warn "Токен не введён. Бот не будет установлен."
            BOT_ENABLED="no"
        else
            log_ok "Токен бота сохранён"
            echo ""
            read -p "Введите ваш Chat ID для уведомлений (необязательно, нажмите Enter для пропуска): " ADMIN_CHAT_ID
            ADMIN_CHAT_ID=${ADMIN_CHAT_ID:-""}
            if [ -n "$ADMIN_CHAT_ID" ]; then
                log_ok "Chat ID для уведомлений: $ADMIN_CHAT_ID"
            fi
        fi
    else
        log_info "Telegram бот не будет установлен"
    fi

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 5: Создание конфигурации
# ============================================================

step_create_config() {
    print_step "5" "Создание конфигурационных файлов"

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/mtproxy"
    mkdir -p "$INSTALL_DIR/webui"
    mkdir -p "$INSTALL_DIR/bot"
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/data"

    # Генерация docker-compose.yml
    log_info "Создание docker-compose.yml..."
    cat > "$INSTALL_DIR/docker-compose.yml" << COMPOSE_EOF
version: '3.8'

services:
  mtproxy:
    image: nineseconds/mtg:2
    container_name: mtproto-proxy
    restart: unless-stopped
    ports:
      - "${PROXY_PORT}:${PROXY_PORT}"
    command: >
      simple-run
      -a ${PROXY_SECRET}
      --prefer-ip=prefer-ipv4
      0.0.0.0:${PROXY_PORT}
    volumes:
      - ./data/mtproxy:/data
    networks:
      - mtproto-net
    healthcheck:
      test: ["CMD", "ss", "-tlnp", "sport", "=:${PROXY_PORT}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  webui:
    build: ./webui
    container_name: mtproto-webui
    restart: unless-stopped
    ports:
      - "${WEBUI_PORT}:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./mtproxy:/app/mtproxy
    environment:
      - PROXY_IP=${SERVER_IP}
      - PROXY_PORT=${PROXY_PORT}
      - FAKE_DOMAIN=${FAKE_DOMAIN}
    depends_on:
      - mtproxy
    networks:
      - mtproto-net

COMPOSE_EOF

    if [[ "$BOT_ENABLED" == "yes" ]]; then
        cat >> "$INSTALL_DIR/docker-compose.yml" << BOT_EOF
  bot:
    build: ./bot
    container_name: mtproto-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_CHAT_ID=${ADMIN_CHAT_ID}
      - PROXY_IP=${SERVER_IP}
      - PROXY_PORT=${PROXY_PORT}
      - FAKE_DOMAIN=${FAKE_DOMAIN}
      - PROXY_SECRET=${PROXY_SECRET}
    depends_on:
      - mtproxy
    networks:
      - mtproto-net

BOT_EOF
    fi

    cat >> "$INSTALL_DIR/docker-compose.yml" << NET_EOF
networks:
  mtproto-net:
    driver: bridge
NET_EOF

    log_ok "docker-compose.yml создан"

    # Генерация конфига mtproxy
    log_info "Создание конфигурации прокси..."
    cat > "$INSTALL_DIR/mtproxy/config.toml" << MTCONF_EOF
# MTProto Proxy Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

[general]
bind_to = "0.0.0.0:${PROXY_PORT}"
secret = "${PROXY_SECRET}"
fake_tls_domain = "${FAKE_DOMAIN}"
prefer_ip = "prefer-ipv4"

[anti_replay]
enabled = true
max_size = 16384

[timeouts]
inactivity = 300
keepalive = 60

[stats]
enabled = true
stats_file = "/data/stats.json"
MTCONF_EOF

    log_ok "Конфигурация прокси создана"

    # Создание пользователей по умолчанию
    log_info "Создание файла пользователей..."
    cat > "$INSTALL_DIR/data/users.json" << USERS_EOF
{
    "users": [
        {
            "id": 1,
            "label": "admin",
            "secret": "${PROXY_SECRET}",
            "enabled": true,
            "created_at": "$(date '+%Y-%m-%d %H:%M:%S')",
            "max_connections": 0,
            "max_ips": 0,
            "data_quota": "0",
            "expires": "",
            "traffic_in": 0,
            "traffic_out": 0,
            "connections": 0
        }
    ],
    "next_id": 2
}
USERS_EOF

    log_ok "Файл пользователей создан"

    # Создание файла настроек
    cat > "$INSTALL_DIR/config/settings.json" << SET_EOF
{
    "proxy_ip": "${SERVER_IP}",
    "proxy_port": ${PROXY_PORT},
    "fake_domain": "${FAKE_DOMAIN}",
    "webui_port": ${WEBUI_PORT},
    "bot_enabled": ${BOT_ENABLED},
    "bot_token": "${BOT_TOKEN}",
    "admin_chat_id": "${ADMIN_CHAT_ID}",
    "auto_heal": true,
    "auto_update": true,
    "backup_enabled": true,
    "backup_interval": "daily",
    "monitor_interval": 300,
    "geoblock": [],
    "ip_whitelist": [],
    "ip_blacklist": [],
    "rate_limit": 100,
    "created_at": "$(date '+%Y-%m-%d %H:%M:%S')"
}
SET_EOF

    log_ok "Файл настроек создан"

    # Список доменов для авто-ротации
    cat > "$INSTALL_DIR/config/domains.txt" << DOM_EOF
cloudflare.com
1c.ru
sberbank.ru
yandex.ru
mail.ru
vk.com
gosuslugi.ru
ok.ru
rambler.ru
rt.com
DOM_EOF

    log_ok "Список доменов создан"

    # GeoIP список
    cat > "$INSTALL_DIR/config/geoblock.txt" << GEO_EOF
# GeoIP блокировка (двухбуквенные коды стран)
# Пример: CN, IR, KP
# Оставьте пустым для отключения
GEO_EOF

    log_ok "GeoIP файл создан"

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 6: Копирование файлов Web UI
# ============================================================

step_copy_webui() {
    print_step "6" "Подготовка Web UI"

    mkdir -p "$INSTALL_DIR/webui"

    # Копируем файлы из текущего репозитория
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -d "$SCRIPT_DIR/webui" ]; then
        cp -r "$SCRIPT_DIR/webui/"* "$INSTALL_DIR/webui/"
        log_ok "Файлы Web UI скопированы"
    else
        log_warn "Файлы Web UI не найдены, создаём минимальную версию..."
        create_minimal_webui
    fi

    read -p "Нажмите Enter для продолжения..."
}

create_minimal_webui() {
    # Создаём минимальный Web UI если файлы не найдены
    cat > "$INSTALL_DIR/webui/Dockerfile" << 'WDOCKER_EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
WDOCKER_EOF

    cat > "$INSTALL_DIR/webui/requirements.txt" << 'WREQ_EOF'
fastapi==0.109.0
uvicorn==0.27.0
jinja2==3.1.3
python-multipart==0.0.6
WREQ_EOF
}

# ============================================================
# ШАГ 7: Копирование файлов бота
# ============================================================

step_copy_bot() {
    if [[ "$BOT_ENABLED" != "yes" ]]; then
        log_info "Telegram бот пропущен"
        return
    fi

    print_step "7" "Подготовка Telegram бота"

    mkdir -p "$INSTALL_DIR/bot"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -d "$SCRIPT_DIR/bot" ]; then
        cp -r "$SCRIPT_DIR/bot/"* "$INSTALL_DIR/bot/"
        log_ok "Файлы бота скопированы"
    fi

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 8: Копирование скриптов
# ============================================================

step_copy_scripts() {
    print_step "8" "Установка вспомогательных скриптов"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -d "$SCRIPT_DIR/scripts" ]; then
        cp "$SCRIPT_DIR/scripts/"* "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/"*.sh
        log_ok "Вспомогательные скрипты установлены"
    fi

    # Установка systemd сервисов
    log_info "Настройка автозапуска..."

    cat > /etc/systemd/system/mtproto-heal.service << 'HEAL_EOF'
[Unit]
Description=MTProto Auto-Heal Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/opt/mtprotoserver/scripts/auto-heal.sh
WorkingDirectory=/opt/mtprotoserver

[Install]
WantedBy=multi-user.target
HEAL_EOF

    cat > /etc/systemd/system/mtproto-heal.timer << 'TIMER_EOF'
[Unit]
Description=MTProto Auto-Heal Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
TIMER_EOF

    systemctl daemon-reload
    systemctl enable mtproto-heal.timer
    systemctl start mtproto-heal.timer

    log_ok "Автозапуск настроен"

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 9: Запуск
# ============================================================

step_start() {
    print_step "9" "Запуск MTProto прокси"

    cd "$INSTALL_DIR"

    log_info "Запуск контейнеров..."
    docker compose pull
    docker compose up -d

    sleep 3

    # Проверка
    if docker compose ps | grep -q "Up"; then
        log_ok "Контейнеры запущены!"
    else
        log_err "Ошибка запуска контейнеров!"
        docker compose logs
        exit 1
    fi

    echo ""
    log_info "Статус контейнеров:"
    docker compose ps

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 10: Итоговая информация
# ============================================================

step_summary() {
    print_step "10" "Установка завершена!"

    print_sep
    echo -e "${GREEN}${E_OK}  MTProtoSERVER успешно установлен!${NC}"
    print_sep
    echo ""

    echo -e "${WHITE}${E_STAR}  ССЫЛКА ДЛЯ ПОДКЛЮЧЕНИЯ:${NC}"
    echo -e "${CYAN}   tg://proxy?server=${SERVER_IP}&port=${PROXY_PORT}&secret=${PROXY_SECRET}${NC}"
    echo ""

    echo -e "${WHITE}${E_NET}  Web Панель управления:${NC}"
    echo -e "${CYAN}   http://${SERVER_IP}:${WEBUI_PORT}${NC}"
    echo ""

    if [[ "$BOT_ENABLED" == "yes" ]]; then
        echo -e "${WHITE}${E_BOT}  Telegram бот:${NC}"
        echo -e "${CYAN}   Токен: ${BOT_TOKEN}${NC}"
        echo -e "   Запустите бота в Telegram"
        echo ""
    fi

    echo -e "${WHITE}${E_FILE}  Каталог установки:${NC}"
    echo -e "   $INSTALL_DIR"
    echo ""

    echo -e "${WHITE}${E_GEAR}  Полезные команды:${NC}"
    echo -e "   ${E_ARROW} Просмотр логов:      ${CYAN}cd $INSTALL_DIR && docker compose logs -f${NC}"
    echo -e "   ${E_ARROW} Перезапуск:          ${CYAN}cd $INSTALL_DIR && docker compose restart${NC}"
    echo -e "   ${E_ARROW} Остановка:           ${CYAN}cd $INSTALL_DIR && docker compose down${NC}"
    echo -e "   ${E_ARROW} Обновление:          ${CYAN}cd $INSTALL_DIR && docker compose pull && docker compose up -d${NC}"
    echo -e "   ${E_ARROW} Статус:              ${CYAN}cd $INSTALL_DIR && docker compose ps${NC}"
    echo ""

    echo -e "${WHITE}${E_SHIELD}  Безопасность:${NC}"
    echo -e "   ${E_WARN}  Не публикуйте ссылку на прокси!"
    echo -e "   ${E_WARN}  Домен маскировки: ${FAKE_DOMAIN}"
    echo -e "   ${E_WARN}  Порт: ${PROXY_PORT} (должен быть открыт в файрволе)"
    echo ""

    print_sep
    echo -e "${GREEN}   Спасибо за использование MTProtoSERVER!${NC}"
    print_sep
    echo ""
}

# ============================================================
# ГЛАВНЫЙ ЦИКЛ
# ============================================================

main() {
    print_header

    echo -e "${WHITE}Добро пожаловать в установщик MTProtoSERVER!${NC}"
    echo -e "Этот скрипт установит полноценный MTProto прокси с:"
    echo -e "  ${E_SHIELD} FakeTLS маскировкой (обход блокировок)"
    echo -e "  ${E_NET} Web панелью управления"
    echo -e "  ${E_BOT} Telegram ботом (опционально)"
    echo -e "  ${E_CHART} Статистикой и мониторингом"
    echo -e "  ${E_LOCK} Мульти-пользовательским доступом"
    echo ""

    read -p "Продолжить установку? [y/n]: " confirm
    confirm=${confirm:-y}
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Установка отменена"
        exit 0
    fi

    step_system_check
    step_install_docker
    step_proxy_config
    step_bot_config
    step_create_config
    step_copy_webui
    step_copy_bot
    step_copy_scripts
    step_start
    step_summary
}

main "$@"
