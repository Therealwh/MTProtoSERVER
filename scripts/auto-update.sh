#!/bin/bash
# Auto-Update скрипт — обновляет образы и перезапускает контейнеры

set -euo pipefail

INSTALL_DIR="/opt/mtprotoserver"
LOG_FILE="$INSTALL_DIR/data/auto-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔄 Проверка обновлений..."

cd "$INSTALL_DIR"

# Pull новых образов
log "⬇️ Загрузка новых образов..."
docker compose pull 2>&1 | tee -a "$LOG_FILE"

# Перезапуск
log "🔄 Перезапуск контейнеров..."
docker compose up -d 2>&1 | tee -a "$LOG_FILE"

log "✅ Обновление завершено"
