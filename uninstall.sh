#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MTProtoSERVER — Полное удаление (ничего не остаётся)
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/mtprotoserver"
AGENT_DIR="/opt/mtg-agent"
FORCE="${1:-}"

echo -e "${RED}⚠️  MTProtoSERVER — ПОЛНОЕ УДАЛЕНИЕ${NC}"
echo -e "${YELLOW}   Все контейнеры, образы, данные, конфиги и сервисы будут удалены${NC}"
echo ""

# Подтверждение
if [[ "$FORCE" == "-y" || "$FORCE" == "-f" || "$FORCE" == "--yes" || "$FORCE" == "--force" ]]; then
    echo -e "${YELLOW}Принудительное удаление...${NC}"
else
    if [ -t 0 ]; then
        read -p "Вы уверены? ВСЁ будет удалено безвозвратно! [y/N]: " confirm
        confirm=${confirm:-N}
    elif [ -t 1 ] && [ -e /dev/tty ]; then
        read -p "Вы уверены? ВСЁ будет удалено безвозвратно! [y/N]: " confirm < /dev/tty
        confirm=${confirm:-N}
    else
        echo -e "${YELLOW}⚠️  Для удаления через pipe:"
        echo -e "   curl -fsSL .../uninstall.sh | sudo bash -s -- -y"
        exit 1
    fi

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Отменено."
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}  Начинаю полное удаление...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Остановка и удаление контейнеров
echo -e "${YELLOW}[1/8] Остановка и удаление контейнеров...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR" 2>/dev/null && docker compose down --remove-orphans 2>/dev/null || true
    cd / 2>/dev/null || true
fi
# Удаляем ВСЕ контейнеры с mtproto/mtg в имени
for c in $(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -iE 'mtproto|mtg|dante|squid' || true); do
    docker rm -f "$c" 2>/dev/null || true
    echo -e "  Удалён контейнер: $c"
done

# 2. Удаление образов
echo -e "${YELLOW}[2/8] Удаление Docker образов...${NC}"
for img in $(docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -iE 'mtproto|mtg|mtprotoserver|dante|squid' || true); do
    docker rmi -f "$img" 2>/dev/null || true
    echo -e "  Удалён образ: $img"
done

# 3. Удаление volumes
echo -e "${YELLOW}[3/8] Удаление Docker volumes...${NC}"
for vol in $(docker volume ls --format '{{.Name}}' 2>/dev/null | grep -iE 'mtproto|mtprotoserver' || true); do
    docker volume rm -f "$vol" 2>/dev/null || true
    echo -e "  Удалён volume: $vol"
done

# 4. Удаление networks
echo -e "${YELLOW}[4/8] Удаление Docker networks...${NC}"
for net in $(docker network ls --format '{{.Name}}' 2>/dev/null | grep -iE 'mtproto|mtprotoserver' || true); do
    docker network rm "$net" 2>/dev/null || true
    echo -e "  Удалена сеть: $net"
done

# 5. Очистка Docker (prune)
echo -e "${YELLOW}[5/8] Очистка Docker (prune)...${NC}"
docker system prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true
echo -e "  ✅ Docker очищен"

# 6. Удаление systemd сервисов
echo -e "${YELLOW}[6/8] Удаление systemd сервисов...${NC}"
systemctl disable mtproto-heal.timer 2>/dev/null || true
systemctl stop mtproto-heal.timer 2>/dev/null || true
rm -f /etc/systemd/system/mtproto-heal.service
rm -f /etc/systemd/system/mtproto-heal.timer
systemctl daemon-reload 2>/dev/null || true
echo -e "  ✅ Systemd сервисы удалены"

# 7. Удаление файлов
echo -e "${YELLOW}[7/8] Удаление файлов...${NC}"
rm -rf "$INSTALL_DIR"
echo -e "  ✅ Удалено: $INSTALL_DIR"

rm -rf "$AGENT_DIR"
echo -e "  ✅ Удалено: $AGENT_DIR"

# 8. Очистка UFW правил (опционально)
echo -e "${YELLOW}[8/8] Очистка правил файрвола...${NC}"
for port in 443 444 445 446 447 448 449 450 8080 1080 3128 9876; do
    ufw delete allow "$port/tcp" 2>/dev/null || true
done
echo -e "  ✅ Правила файрвола удалены"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ MTProtoSERVER ПОЛНОСТЬЮ УДАЛЁН!${NC}"
echo -e "${GREEN}   Не осталось: контейнеров, образов, volumes, сетей, файлов, сервисов${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
