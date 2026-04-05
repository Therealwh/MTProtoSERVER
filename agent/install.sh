#!/usr/bin/env bash
set -euo pipefail

# MTG Agent Installer
# Usage: curl -fsSL ... | bash -s -- --port 9876 --token YOUR_TOKEN

PORT=9876
TOKEN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --token) TOKEN="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TOKEN" ]; then
    echo "Error: --token is required"
    exit 1
fi

echo "🔧 Installing MTG Agent..."

# Install Docker if needed
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Create agent directory
mkdir -p /opt/mtg-agent

# Create docker-compose
cat > /opt/mtg-agent/docker-compose.yml << EOF
version: '3.8'
services:
  mtg-agent:
    image: python:3.11-slim
    container_name: mtg-agent
    restart: unless-stopped
    ports:
      - "${PORT}:9876"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./agent.py:/app/agent.py
    environment:
      - AGENT_TOKEN=${TOKEN}
    working_dir: /app
    command: >
      bash -c "pip install --no-cache-dir fastapi uvicorn docker psutil pydantic &&
               uvicorn agent:app --host 0.0.0.0 --port 9876"
    networks:
      - agent-net
networks:
  agent-net:
    driver: bridge
EOF

# Download agent
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/agent/agent.py -o /opt/mtg-agent/agent.py

# Start
cd /opt/mtg-agent
docker compose up -d

echo "✅ MTG Agent installed!"
echo "   Port: $PORT"
echo "   Health: http://localhost:$PORT/health"
echo "   Token: $TOKEN"
