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
FORCE="${1:-}"

echo -e "${RED}⚠️  MTProtoSERVER — Удаление${NC}"
echo ""

# Если передан флаг -y или -f — удаляем без подтверждения
if [[ "$FORCE" == "-y" || "$FORCE" == "-f" || "$FORCE" == "--yes" || "$FORCE" == "--force" ]]; then
    echo -e "${YELLOW}Принудительное удаление...${NC}"
else
    # Проверяем есть ли терминал (не pipe)
    if [ -t 0 ]; then
        read -p "Вы уверены? Все данные будут удалены! [y/N]: " confirm
        confirm=${confirm:-N}
    else
        # Запущен через curl | bash — спрашиваем через /dev/tty
        if [ -t 1 ] && [ -e /dev/tty ]; then
            read -p "Вы уверены? Все данные будут удалены! [y/N]: " confirm < /dev/tty
            confirm=${confirm:-N}
        else
            echo -e "${YELLOW}⚠️  Для удаления через pipe используйте:"
            echo -e "   curl -fsSL .../uninstall.sh | sudo bash -s -- -y"
            echo -e "   или скачайте и запустите с флагом -y"
            echo ""
            echo -e "Отменено. Для принудительного удаления добавьте -y"
            exit 1
        fi
    fi

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Отменено."
        exit 0
    fi
fi

echo "Остановка контейнеров..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR" 2>/dev/null && docker compose down 2>/dev/null || true
fi

echo "Удаление контейнеров..."
docker rm -f $(docker ps -a --filter "name=mtproto-" --format '{{.Names}}') 2>/dev/null || true

echo "Удаление образов..."
docker rmi $(docker images --filter "reference=mtproto-*" --format '{{.Repository}}') 2>/dev/null || true

echo "Удаление systemd сервисов..."
systemctl disable mtproto-heal.timer 2>/dev/null || true
systemctl stop mtproto-heal.timer 2>/dev/null || true
rm -f /etc/systemd/system/mtproto-heal.service
rm -f /etc/systemd/system/mtproto-heal.timer
systemctl daemon-reload 2>/dev/null || true

echo "Удаление файлов..."
rm -rf "$INSTALL_DIR"

echo -e "${GREEN}✅ MTProtoSERVER полностью удалён!${NC}"
