#!/bin/bash
# Auto-Heal скрипт — проверяет и перезапускает упавшие контейнеры

set -euo pipefail

INSTALL_DIR="/opt/mtprotoserver"
LOG_FILE="$INSTALL_DIR/data/auto-heal.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_container() {
    local container=$1
    local running
    running=$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || echo "false")

    if [ "$running" != "true" ]; then
        log "❌ Контейнер $container не работает! Перезапуск..."
        cd "$INSTALL_DIR"
        docker compose up -d "$container"
        sleep 3

        running=$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || echo "false")
        if [ "$running" = "true" ]; then
            log "✅ Контейнер $container перезапущен успешно"
        else
            log "❌ Не удалось перезапустить $container!"
        fi
    else
        log "✅ Контейнер $container работает"
    fi
}

log "🔄 Auto-Heal проверка..."

check_container "mtproto-proxy"
check_container "mtproto-webui"

if docker compose ps | grep -q "mtproto-bot"; then
    check_container "mtproto-bot"
fi

log "✅ Проверка завершена"
