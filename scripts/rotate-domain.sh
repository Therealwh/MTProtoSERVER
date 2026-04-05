#!/bin/bash
# Скрипт автоматической ротации домена FakeTLS

set -euo pipefail

INSTALL_DIR="/opt/mtprotoserver"
DOMAINS_FILE="$INSTALL_DIR/config/domains.txt"
CONFIG_FILE="$INSTALL_DIR/config/settings.json"
LOG_FILE="$INSTALL_DIR/data/rotate-domain.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Читаем текущий домен
CURRENT_DOMAIN=$(grep -o '"fake_domain"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
log "Текущий домен: $CURRENT_DOMAIN"

# Выбираем следующий домен
DOMAINS=()
while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue
    DOMAINS+=("$line")
done < "$DOMAINS_FILE"

# Находим следующий домен
NEXT_INDEX=0
for i in "${!DOMAINS[@]}"; do
    if [ "${DOMAINS[$i]}" = "$CURRENT_DOMAIN" ]; then
        NEXT_INDEX=$(( (i + 1) % ${#DOMAINS[@]} ))
        break
    fi
done

NEW_DOMAIN="${DOMAINS[$NEXT_INDEX]}"
log "Новый домен: $NEW_DOMAIN"

# Обновляем конфиг
sed -i "s/\"fake_domain\": \"[^\"]*\"/\"fake_domain\": \"$NEW_DOMAIN\"/" "$CONFIG_FILE"

# Генерируем новый секрет
DOMAIN_HEX=$(echo -n "$NEW_DOMAIN" | xxd -p | tr -d '\n')
RANDOM_PART=$(openssl rand -hex 14)
NEW_SECRET="ee${RANDOM_PART}${DOMAIN_HEX}"

# Обновляем docker-compose
sed -i "s/secret: .*/secret: \"$NEW_SECRET\"/" "$INSTALL_DIR/docker-compose.yml"

# Перезапускаем прокси
cd "$INSTALL_DIR"
docker compose up -d mtproto-proxy

log "✅ Домен изменён на $NEW_DOMAIN"
log "✅ Новый секрет: $NEW_SECRET"
