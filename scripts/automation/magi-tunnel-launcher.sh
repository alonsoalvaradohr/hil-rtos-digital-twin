#!/bin/bash
# MAGI RESILIENT TUNNEL LAUNCHER
# Si existe token de Cloudflare Zero Trust (Named Tunnel), ejecuta el túnel permanente.
# En caso contrario, ejecuta el túnel rápido con auto-recuperación de conexión.

TOKEN_FILE="/etc/cloudflared/token"
DOMAIN_FILE="/etc/cloudflared/domain"

if [ -s "$TOKEN_FILE" ]; then
    TOKEN=$(head -n 1 "$TOKEN_FILE" | tr -d '\r\n[:space:]')
    if [ -s "$DOMAIN_FILE" ]; then
        DOMAIN=$(head -n 1 "$DOMAIN_FILE" | tr -d '\r\n[:space:]')
        echo "https://${DOMAIN}" > /home/alonso/magi_url.txt
    fi
    exec /usr/local/bin/cloudflared tunnel run --token "$TOKEN"
else
    exec /usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8088 --no-autoupdate
fi
