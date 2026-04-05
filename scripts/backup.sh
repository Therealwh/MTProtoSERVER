#!/bin/bash
# Backup скрипт — резервное копирование конфигураций

set -euo pipefail

INSTALL_DIR="/opt/mtprotoserver"
BACKUP_DIR="$INSTALL_DIR/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "📦 Создание бэкапа..."

# Файлы для бэкапа
FILES_TO_BACKUP=(
    "$INSTALL_DIR/config"
    "$INSTALL_DIR/data"
    "$INSTALL_DIR/mtproxy"
    "$INSTALL_DIR/docker-compose.yml"
)

tar -czf "$BACKUP_FILE" "${FILES_TO_BACKUP[@]}" 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Бэкап создан: $BACKUP_FILE ($BACKUP_SIZE)"

# Удаление старых бэкапов (оставить последние 10)
cd "$BACKUP_DIR"
ls -t backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
echo "🗑️ Старые бэкапы удалены"
