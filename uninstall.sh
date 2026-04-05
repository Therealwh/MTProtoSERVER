#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER - Скрипт удаления
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/mtprotoserver"

echo -e "${RED}⚠️  MTProtoSERVER — Удаление${NC}"
echo ""

read -p "Вы уверены? Все данные будут удалены! [y/N]: " confirm
confirm=${confirm:-N}

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Отменено."
    exit 0
fi

echo "Остановка контейнеров..."
cd "$INSTALL_DIR" 2>/dev/null && docker compose down 2>/dev/null || true

echo "Удаление контейнеров..."
docker rm -f mtproto-proxy mtproto-webui mtproto-bot 2>/dev/null || true

echo "Удаление образов..."
docker rmi mtproto-webui mtproto-bot 2>/dev/null || true

echo "Удаление systemd сервисов..."
systemctl disable mtproto-heal.timer 2>/dev/null || true
systemctl stop mtproto-heal.timer 2>/dev/null || true
rm -f /etc/systemd/system/mtproto-heal.service
rm -f /etc/systemd/system/mtproto-heal.timer
systemctl daemon-reload 2>/dev/null || true

echo "Удаление файлов..."
rm -rf "$INSTALL_DIR"

echo -e "${GREEN}✅ MTProtoSERVER полностью удалён!${NC}"
