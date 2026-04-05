#!/bin/bash
# Мониторинг доступности прокси

set -euo pipefail

INSTALL_DIR="/opt/mtprotoserver"
CONFIG_FILE="$INSTALL_DIR/config/settings.json"
LOG_FILE="$INSTALL_DIR/data/monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Получаем настройки
PROXY_IP=$(grep -o '"proxy_ip"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
PROXY_PORT=$(grep -o '"proxy_port"[[:space:]]*:[[:space:]]*[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*$')
BOT_TOKEN=$(grep -o '"bot_token"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
ADMIN_CHAT_ID=$(grep -o '"admin_chat_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)

log "🔍 Проверка прокси $PROXY_IP:$PROXY_PORT..."

# Проверка порта
if timeout 5 bash -c "echo > /dev/tcp/$PROXY_IP/$PROXY_PORT" 2>/dev/null; then
    log "✅ Прокси доступен"
else
    log "❌ Прокси НЕ доступен! Перезапуск..."

    cd "$INSTALL_DIR"
    docker compose restart mtproto-proxy

    sleep 5

    if timeout 5 bash -c "echo > /dev/tcp/$PROXY_IP/$PROXY_PORT" 2>/dev/null; then
        log "✅ Пркси перезапущен и доступен"
    else
        log "❌ Прокси всё ещё недоступен после перезапуска!"

        # Уведомление через бота
        if [ -n "$BOT_TOKEN" ] && [ -n "$ADMIN_CHAT_ID" ]; then
            curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
                -d "chat_id=${ADMIN_CHAT_ID}" \
                -d "text=🚨 *КРИТИЧЕСКАЯ ОШИБКА!*%0A%0AПрокси $PROXY_IP:$PROXY_PORT недоступен после перезапуска!" \
                -d "parse_mode=Markdown" 2>/dev/null || true
        fi
    fi
fi
