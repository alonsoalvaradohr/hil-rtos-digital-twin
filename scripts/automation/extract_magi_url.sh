#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
sleep 3
# Si existe configuración de dominio estático persistente
if [ -s /etc/cloudflared/domain ]; then
    DOMAIN=$(head -n 1 /etc/cloudflared/domain | tr -d '\r\n[:space:]')
    if [ -n "$DOMAIN" ]; then
        echo "https://${DOMAIN}" > [HOME_REDACTED]
        echo "[MAGI-TUNNEL] Dominio estatico/persistente activo: https://${DOMAIN}"
        exit 0
    fi
fi

for i in $(seq 1 30); do
    URL=$(journalctl -u magi-tunnel.service --no-pager -n 45 2>/dev/null | grep -oE "https://[a-zA-Z0-9-]+\.tunnel-provider\.com" | grep -v "api.tunnel.example.org" | tail -1)
    if [ -n "$URL" ]; then
        echo "$URL" > [HOME_REDACTED]
        echo "[MAGI-TUNNEL] URL capturada: $URL"
        exit 0
    fi
    sleep 1
done
exit 0
