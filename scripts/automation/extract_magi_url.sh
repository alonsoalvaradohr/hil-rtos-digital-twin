#!/bin/bash
sleep 3
for i in $(seq 1 25); do
    URL=$(journalctl -u magi-tunnel.service --no-pager -n 35 2>/dev/null | grep -oE "https://[a-zA-Z0-9-]+\.tunnel-provider\.com" | grep -v "api.tunnel.example.org" | tail -1)
    if [ -n "$URL" ]; then
        echo "$URL" > [HOME_REDACTED]
        echo "[MAGI-URLL URL capturada: $URL"
        exit 0
    fi
    sleep 1
done
