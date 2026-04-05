#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER - Полный установщик MTProto прокси
# Версия: 1.1.0
# Дата: 2026-04-05
# Поддержка: FakeTLS, Multi-User, Multi-Proxy, Web UI, Telegram Bot
# ============================================================

REPO_URL="https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main"

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
PROXY_COUNT=1
declare -a PROXY_PORTS=()
declare -a PROXY_DOMAINS=()
declare -a PROXY_SECRETS=()
declare -a PROXY_LABELS=()

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
    echo -e "${CYAN}   Версия 1.1.0 | 2026 | Multi-Proxy + FakeTLS + Web UI + Bot${NC}"
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
        if ! docker compose version &>/dev/null 2>&1; then
            log_warn "Docker Compose не найден, устанавливаем..."
        else
            log_ok "Docker Compose: $(docker compose version)"
            read -p "Нажмите Enter для продолжения..."
            return
        fi
    fi

    log_info "Установка Docker..."

    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 2>/dev/null || true
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
    echo -e "   Прокси будет маскироваться под обычный HTTPS к выбранному домену"
    echo -e "   Для DPI это выглядит как посещение обычного сайта"
    echo -e "   Вы можете создать несколько прокси на разных портах с разными доменами"
    echo ""

    # Сколько прокси создать
    read -p "Сколько прокси серверов создать? [1-10] (по умолчанию 1): " proxy_count_input
    PROXY_COUNT=${proxy_count_input:-1}
    if [ "$PROXY_COUNT" -lt 1 ]; then PROXY_COUNT=1; fi
    if [ "$PROXY_COUNT" -gt 10 ]; then PROXY_COUNT=10; fi
    log_ok "Будет создано прокси: $PROXY_COUNT"
    echo ""

    for i in $(seq 1 $PROXY_COUNT); do
        print_sep
        echo -e "${WHITE}${E_STAR}  Прокси #${i} из ${PROXY_COUNT}${NC}"
        print_sep
        echo ""

        # Метка
        read -p "Метка прокси (например: main, backup, friends): " proxy_label
        proxy_label=${proxy_label:-"proxy${i}"}
        PROXY_LABELS+=("$proxy_label")
        log_ok "Метка: $proxy_label"
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

        read -p "Выберите домен для прокси #${i} [1-8] (по умолчанию 1): " domain_choice
        domain_choice=${domain_choice:-1}

        case $domain_choice in
            1) current_domain="cloudflare.com" ;;
            2) current_domain="1c.ru" ;;
            3) current_domain="sberbank.ru" ;;
            4) current_domain="yandex.ru" ;;
            5) current_domain="mail.ru" ;;
            6) current_domain="vk.com" ;;
            7) current_domain="gosuslugi.ru" ;;
            8)
                read -p "Введите домен для маскировки: " current_domain
                ;;
            *) current_domain="cloudflare.com" ;;
        esac

        PROXY_DOMAINS+=("$current_domain")
        log_ok "Домен маскировки #${i}: ${E_NET} $current_domain"
        echo ""

        # Порт прокси
        default_port=$((443 + i - 1))
        read -p "Порт для прокси #${i} [${default_port}]: " port_input
        current_port=${port_input:-$default_port}

        # Проверка что порт не занят
        while ss -tlnp 2>/dev/null | grep -q ":${current_port} "; do
            log_warn "Порт ${current_port} уже занят!"
            read -p "Введите другой порт: " current_port
        done

        PROXY_PORTS+=("$current_port")
        log_ok "Порт прокси #${i}: $current_port"
        echo ""

        # Генерация секрета
        current_secret=""
        local domain_hex=$(echo -n "$current_domain" | xxd -p | tr -d '\n')
        local random_part=$(openssl rand -hex 14)
        current_secret="ee${random_part}${domain_hex}"
        PROXY_SECRETS+=("$current_secret")
        log_ok "FakeTLS секрет #${i} сгенерирован ${E_KEY}"
        echo ""
    done

    # Первый прокси — основной
    PROXY_PORT="${PROXY_PORTS[0]}"
    FAKE_DOMAIN="${PROXY_DOMAINS[0]}"
    PROXY_SECRET="${PROXY_SECRETS[0]}"

    # Порт Web UI
    read -p "Порт Web UI [8080]: " webui_input
    WEBUI_PORT=${webui_input:-8080}
    log_ok "Порт Web UI: $WEBUI_PORT"
    echo ""

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
    echo -e "   Только админ сможет использовать бота"
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

            # Автоматическое получение Chat ID
            echo -e "${WHITE}${E_PHONE}  Получение Chat ID админа...${NC}"
            echo -e "   ${E_ARROW} Откройте вашего бота в Telegram"
            echo -e "   ${E_ARROW} Напишите команду /start"
            echo -e "   ${E_ARROW} Затем нажмите Enter здесь"
            echo ""
            read -p "Вы написали /start в бота? [y/n]: " wrote_start
            wrote_start=${wrote_start:-n}

            if [[ "$wrote_start" =~ ^[Yy]$ ]]; then
                log_info "Получение Chat ID через Telegram API..."
                # Получаем последние обновления от бота
                local updates
                updates=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" 2>/dev/null || echo "")

                if [ -n "$updates" ] && echo "$updates" | grep -q '"chat"'; then
                    # Извлекаем Chat ID из последнего сообщения
                    ADMIN_CHAT_ID=$(echo "$updates" | grep -o '"chat":{"id":[0-9-]*' | tail -1 | grep -o '[0-9-]*$')

                    if [ -n "$ADMIN_CHAT_ID" ]; then
                        log_ok "Chat ID получен автоматически: ${ADMIN_CHAT_ID}"
                        echo -e "   ${E_LOCK} Только этот пользователь сможет использовать бота"
                    else
                        log_warn "Не удалось получить Chat ID автоматически"
                        read -p "Введите Chat ID вручную: " ADMIN_CHAT_ID
                    fi
                else
                    log_warn "Бот не получил сообщений. Возможно, вы ещё не написали /start"
                    echo ""
                    echo -e "${YELLOW}Повторите:${NC}"
                    echo -e "  1. Найдите бота в Telegram"
                    echo -e "  2. Напишите /start"
                    echo -e "  3. Затем нажмите Enter"
                    echo ""
                    read -p "Готово? [y/n]: " retry_start
                    retry_start=${retry_start:-n}

                    if [[ "$retry_start" =~ ^[Yy]$ ]]; then
                        updates=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" 2>/dev/null || echo "")
                        if [ -n "$updates" ] && echo "$updates" | grep -q '"chat"'; then
                            ADMIN_CHAT_ID=$(echo "$updates" | grep -o '"chat":{"id":[0-9-]*' | tail -1 | grep -o '[0-9-]*$')
                            if [ -n "$ADMIN_CHAT_ID" ]; then
                                log_ok "Chat ID получен автоматически: ${ADMIN_CHAT_ID}"
                            else
                                log_warn "Не удалось получить Chat ID"
                                read -p "Введите Chat ID вручную: " ADMIN_CHAT_ID
                            fi
                        else
                            log_warn "Всё ещё нет сообщений. Введите Chat ID вручную."
                            echo -e "   ${E_INFO} Как узнать: напишите @userinfobot в Telegram"
                            read -p "Chat ID: " ADMIN_CHAT_ID
                        fi
                    else
                        log_warn "Введите Chat ID вручную"
                        echo -e "   ${E_INFO} Как узнать: напишите @userinfobot в Telegram"
                        read -p "Chat ID: " ADMIN_CHAT_ID
                    fi
                fi
            else
                log_info "Введите Chat ID вручную"
                echo -e "   ${E_INFO} Как узнать: напишите @userinfobot в Telegram"
                read -p "Chat ID: " ADMIN_CHAT_ID
            fi

            ADMIN_CHAT_ID=${ADMIN_CHAT_ID:-""}
            if [ -n "$ADMIN_CHAT_ID" ]; then
                log_ok "Admin Chat ID: $ADMIN_CHAT_ID"
                log_ok "Только этот пользователь сможет управлять ботом"
            fi
        fi
    else
        log_info "Telegram бот не будет установлен"
    fi

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 5: Скачивание файлов с GitHub
# ============================================================

step_download_files() {
    print_step "5" "Скачивание файлов проекта"

    log_info "Скачивание файлов с GitHub..."

    # Создаём временную директорию
    local tmp_dir=$(mktemp -d)

    # Список файлов для скачивания
    local files=(
        "webui/Dockerfile"
        "webui/requirements.txt"
        "webui/app.py"
        "webui/templates/base.html"
        "webui/templates/index.html"
        "webui/templates/users.html"
        "webui/templates/proxies.html"
        "webui/templates/stats.html"
        "webui/templates/settings.html"
        "webui/templates/diagnostics.html"
        "webui/static/css/style.css"
        "webui/static/js/app.js"
        "bot/Dockerfile"
        "bot/requirements.txt"
        "bot/bot.py"
        "scripts/auto-heal.sh"
        "scripts/auto-update.sh"
        "scripts/backup.sh"
        "scripts/health-check.sh"
        "scripts/monitor.sh"
        "scripts/rotate-domain.sh"
        "scripts/speedtest.sh"
        "scripts/add-proxy.sh"
        "scripts/remove-proxy.sh"
    )

    local downloaded=0
    local failed=0

    for file in "${files[@]}"; do
        local dir=$(dirname "$file")
        mkdir -p "$tmp_dir/$dir"

        if curl -fsSL -o "$tmp_dir/$file" "${REPO_URL}/${file}" 2>/dev/null; then
            downloaded=$((downloaded + 1))
        else
            log_warn "Не удалось скачать: $file"
            failed=$((failed + 1))
        fi
    done

    log_ok "Скачано: $downloaded файлов, ошибок: $failed"

    # Сохраняем во временную директорию для использования позже
    DOWNLOAD_TMP_DIR="$tmp_dir"

    read -p "Нажмите Enter для продолжения..."
}

# ============================================================
# ШАГ 6: Создание конфигурации
# ============================================================

step_create_config() {
    print_step "6" "Создание конфигурационных файлов"

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/mtproxy"
    mkdir -p "$INSTALL_DIR/webui"
    mkdir -p "$INSTALL_DIR/bot"
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/data"

    # Генерация docker-compose.yml с поддержкой нескольких прокси
    log_info "Создание docker-compose.yml..."

    cat > "$INSTALL_DIR/docker-compose.yml" << COMPOSE_HEADER_EOF
version: '3.8'

services:
COMPOSE_HEADER_EOF

    # Добавляем каждый прокси
    for i in $(seq 0 $((PROXY_COUNT - 1))); do
        local p_port="${PROXY_PORTS[$i]}"
        local p_secret="${PROXY_SECRETS[$i]}"
        local p_label="${PROXY_LABELS[$i]}"
        local container_name="mtproto-proxy-${p_label}"

        cat >> "$INSTALL_DIR/docker-compose.yml" << PROXY_EOF
  mtproxy-${p_label}:
    image: nineseconds/mtg:2
    container_name: ${container_name}
    restart: unless-stopped
    ports:
      - "${p_port}:${p_port}"
    command: >
      simple-run
      -a ${p_secret}
      --prefer-ip=prefer-ipv4
      0.0.0.0:${p_port}
    volumes:
      - ./data/mtproxy-${p_label}:/data
    networks:
      - mtproto-net
    healthcheck:
      test: ["CMD", "ss", "-tlnp", "sport", "=:${p_port}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

PROXY_EOF
    done

    # Web UI
    cat >> "$INSTALL_DIR/docker-compose.yml" << WEBUI_EOF
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
      - PROXY_COUNT=${PROXY_COUNT}
    depends_on:
$(for i in $(seq 0 $((PROXY_COUNT - 1))); do echo "      - mtproxy-${PROXY_LABELS[$i]}"; done)
    networks:
      - mtproto-net

WEBUI_EOF

    # Bot
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
      - PROXY_COUNT=${PROXY_COUNT}
    depends_on:
$(for i in $(seq 0 $((PROXY_COUNT - 1))); do echo "      - mtproxy-${PROXY_LABELS[$i]}"; done)
    networks:
      - mtproto-net

BOT_EOF
    fi

    # Networks
    cat >> "$INSTALL_DIR/docker-compose.yml" << NET_EOF
networks:
  mtproto-net:
    driver: bridge
NET_EOF

    log_ok "docker-compose.yml создан с ${PROXY_COUNT} прокси"

    # Генерация конфига mtproxy (для первого прокси)
    log_info "Создание конфигурации прокси..."
    cat > "$INSTALL_DIR/mtproxy/config.toml" << MTCONF_EOF
# MTProto Proxy Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
# Proxies: ${PROXY_COUNT}

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

    # Конфиги для дополнительных прокси
    for i in $(seq 1 $((PROXY_COUNT - 1))); do
        local p_port="${PROXY_PORTS[$i]}"
        local p_secret="${PROXY_SECRETS[$i]}"
        local p_domain="${PROXY_DOMAINS[$i]}"
        local p_label="${PROXY_LABELS[$i]}"
        mkdir -p "$INSTALL_DIR/mtproxy/${p_label}"
        cat > "$INSTALL_DIR/mtproxy/${p_label}/config.toml" << MTCONF2_EOF
# MTProto Proxy: ${p_label}
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

[general]
bind_to = "0.0.0.0:${p_port}"
secret = "${p_secret}"
fake_tls_domain = "${p_domain}"
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
MTCONF2_EOF
    done

    log_ok "Конфигурация прокси создана"

    # Создание файла прокси-инстансов
    log_info "Создание файла прокси-инстансов..."
    echo "{" > "$INSTALL_DIR/data/proxies.json"
    echo '    "proxies": [' >> "$INSTALL_DIR/data/proxies.json"
    for i in $(seq 0 $((PROXY_COUNT - 1))); do
        local comma=""
        if [ $i -lt $((PROXY_COUNT - 1)) ]; then comma=","; fi
        cat >> "$INSTALL_DIR/data/proxies.json" << PENTRY_EOF
        {
            "id": $((i + 1)),
            "label": "${PROXY_LABELS[$i]}",
            "port": ${PROXY_PORTS[$i]},
            "domain": "${PROXY_DOMAINS[$i]}",
            "secret": "${PROXY_SECRETS[$i]}",
            "enabled": true,
            "created_at": "$(date '+%Y-%m-%d %H:%M:%S')",
            "connections": 0,
            "traffic_in": 0,
            "traffic_out": 0
        }${comma}
PENTRY_EOF
    done
    echo '    ],' >> "$INSTALL_DIR/data/proxies.json"
    echo "    \"next_id\": $((PROXY_COUNT + 1))" >> "$INSTALL_DIR/data/proxies.json"
    echo "}" >> "$INSTALL_DIR/data/proxies.json"

    log_ok "Файл прокси-инстансов создан (${PROXY_COUNT} прокси)"

    # Создание пользователей по умолчанию
    log_info "Создание файла пользователей..."
    cat > "$INSTALL_DIR/data/users.json" << USERS_EOF
{
    "users": [
        {
            "id": 1,
            "label": "admin",
            "proxy_id": 1,
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
    "proxy_count": ${PROXY_COUNT},
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
# ШАГ 7: Копирование скачанных файлов
# ============================================================

step_copy_files() {
    print_step "7" "Установка файлов проекта"

    if [ -n "${DOWNLOAD_TMP_DIR:-}" ] && [ -d "$DOWNLOAD_TMP_DIR" ]; then
        # Копируем webui
        if [ -d "$DOWNLOAD_TMP_DIR/webui" ]; then
            cp -r "$DOWNLOAD_TMP_DIR/webui/"* "$INSTALL_DIR/webui/"
            log_ok "Файлы Web UI установлены"
        fi

        # Копируем bot
        if [ -d "$DOWNLOAD_TMP_DIR/bot" ]; then
            cp -r "$DOWNLOAD_TMP_DIR/bot/"* "$INSTALL_DIR/bot/"
            log_ok "Файлы бота установлены"
        fi

        # Копируем scripts
        if [ -d "$DOWNLOAD_TMP_DIR/scripts" ]; then
            cp "$DOWNLOAD_TMP_DIR/scripts/"* "$INSTALL_DIR/scripts/"
            chmod +x "$INSTALL_DIR/scripts/"*.sh
            log_ok "Вспомогательные скрипты установлены"
        fi

        # Очищаем временную директорию
        rm -rf "$DOWNLOAD_TMP_DIR"
    else
        log_warn "Файлы не были скачаны. Создаём минимальные версии..."
        create_minimal_files
    fi

    read -p "Нажмите Enter для продолжения..."
}

create_minimal_files() {
    # Минимальный Web UI
    mkdir -p "$INSTALL_DIR/webui/templates" "$INSTALL_DIR/webui/static/css" "$INSTALL_DIR/webui/static/js"

    cat > "$INSTALL_DIR/webui/Dockerfile" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    cat > "$INSTALL_DIR/webui/requirements.txt" << 'EOF'
fastapi==0.109.0
uvicorn==0.27.0
jinja2==3.1.3
python-multipart==0.0.6
qrcode==7.4.2
pillow==10.2.0
psutil==5.9.8
EOF

    # Минимальный бот
    mkdir -p "$INSTALL_DIR/bot"

    cat > "$INSTALL_DIR/bot/Dockerfile" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
EOF

    cat > "$INSTALL_DIR/bot/requirements.txt" << 'EOF'
python-telegram-bot==21.0.1
qrcode==7.4.2
pillow==10.2.0
requests==2.31.0
EOF

    log_warn "Созданы минимальные файлы. Рекомендуется скачать полные с GitHub."
}

# ============================================================
# ШАГ 8: Настройка автозапуска
# ============================================================

step_setup_autostart() {
    print_step "8" "Настройка автозапуска"

    log_info "Настройка systemd сервисов..."

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

    sleep 5

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

    echo -e "${WHITE}${E_STAR}  ССЫЛКИ ДЛЯ ПОДКЛЮЧЕНИЯ (${PROXY_COUNT} прокси):${NC}"
    echo ""
    for i in $(seq 0 $((PROXY_COUNT - 1))); do
        echo -e "  ${E_ARROW} ${CYAN}${PROXY_LABELS[$i]}${NC}"
        echo -e "     Порт: ${PROXY_PORTS[$i]} | Домен: ${PROXY_DOMAINS[$i]}"
        echo -e "     ${CYAN}tg://proxy?server=${SERVER_IP}&port=${PROXY_PORTS[$i]}&secret=${PROXY_SECRETS[$i]}${NC}"
        echo ""
    done

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
    echo -e "   ${E_ARROW} Добавить прокси:     ${CYAN}bash $INSTALL_DIR/scripts/add-proxy.sh${NC}"
    echo -e "   ${E_ARROW} Удалить прокси:      ${CYAN}bash $INSTALL_DIR/scripts/remove-proxy.sh <label>${NC}"
    echo ""

    echo -e "${WHITE}${E_SHIELD}  Безопасность:${NC}"
    echo -e "   ${E_WARN}  Не публикуйте ссылки на прокси!"
    for i in $(seq 0 $((PROXY_COUNT - 1))); do
        echo -e "   ${E_WARN}  ${PROXY_LABELS[$i]}: домен=${PROXY_DOMAINS[$i]}, порт=${PROXY_PORTS[$i]}"
    done
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
    echo -e "  ${E_NET} Несколькими прокси (разные порты/домены)"
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
    step_download_files
    step_create_config
    step_copy_files
    step_setup_autostart
    step_start
    step_summary
}

main "$@"
