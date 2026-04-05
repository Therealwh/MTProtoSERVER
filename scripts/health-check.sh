#!/bin/bash
# Health Check — полная диагностика системы

set -euo pipefail

echo "================================================"
echo "  MTProtoSERVER — Health Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

INSTALL_DIR="/opt/mtprotoserver"
ERRORS=0

check() {
    local name=$1
    local result=$2
    if [ "$result" = "0" ]; then
        echo "✅ $name"
    else
        echo "❌ $name"
        ERRORS=$((ERRORS + 1))
    fi
}

# Docker
docker info &>/dev/null
check "Docker запущен" $?

# Контейнеры
for container in mtproto-proxy mtproto-webui; do
    if docker ps --format '{{.Names}}' | grep -q "$container"; then
        check "Контейнер $container работает" 0
    else
        check "Контейнер $container работает" 1
    fi
done

# Порт 443
if ss -tlnp | grep -q ":443 "; then
    check "Порт 443 слушается" 0
else
    check "Порт 443 слушается" 1
fi

# Конфигурация
if [ -f "$INSTALL_DIR/config/settings.json" ]; then
    check "Конфигурация существует" 0
else
    check "Конфигурация существует" 1
fi

# Пользователи
if [ -f "$INSTALL_DIR/data/users.json" ]; then
    USERS_COUNT=$(grep -o '"id"' "$INSTALL_DIR/data/users.json" | wc -l)
    check "База пользователей ($USERS_COUNT пользователей)" 0
else
    check "База пользователей" 1
fi

# Диск
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 90 ]; then
    check "Диск свободен ($DISK_USAGE% использовано)" 0
else
    check "Диск свободен ($DISK_USAGE% использовано)" 1
fi

# RAM
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -lt 90 ]; then
    check "RAM свободна ($MEM_USAGE% использовано)" 0
else
    check "RAM свободна ($MEM_USAGE% использовано)" 1
fi

# Логи
if [ -d "$INSTALL_DIR/data" ]; then
    LOG_SIZE=$(du -sm "$INSTALL_DIR/data" 2>/dev/null | cut -f1)
    check "Размер данных: ${LOG_SIZE}MB" 0
fi

echo ""
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ Все проверки пройдены!"
else
    echo "  ⚠️ Обнаружено проблем: $ERRORS"
fi
echo "================================================"
