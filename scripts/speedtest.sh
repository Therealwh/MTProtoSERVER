#!/bin/bash
# Speedtest — проверка скорости соединения

set -euo pipefail

echo "🚀 MTProtoSERVER Speedtest"
echo "========================"
echo ""

# Проверка download
echo "⬇️  Тест загрузки..."
DOWNLOAD_SPEED=$(curl -s -o /dev/null -w "%{speed_download}" https://speed.cloudflare.com/__down?bytes=10000000 2>/dev/null || echo "0")
DOWNLOAD_MBIT=$(echo "$DOWNLOAD_SPEED * 8 / 1000000" | bc 2>/dev/null || echo "N/A")
echo "   Скорость загрузки: ${DOWNLOAD_MBIT} Mbit/s"

# Проверка upload
echo "⬆️  Тест отдачи..."
UPLOAD_SPEED=$(curl -s -o /dev/null -w "%{speed_upload}" -X POST -d "$(head -c 1000000 /dev/urandom | base64 | head -c 1000000)" https://speed.cloudflare.com/__up 2>/dev/null || echo "0")
UPLOAD_MBIT=$(echo "$UPLOAD_SPEED * 8 / 1000000" | bc 2>/dev/null || echo "N/A")
echo "   Скорость отдачи: ${UPLOAD_MBIT} Mbit/s"

# Пинг
echo "📡 Тест задержки..."
PING_AVG=$(ping -c 4 1.1.1.1 2>/dev/null | tail -1 | awk -F'/' '{print $5}' || echo "N/A")
echo "   Средний пинг до 1.1.1.1: ${PING_AVG} ms"

echo ""
echo "✅ Speedtest завершён"
