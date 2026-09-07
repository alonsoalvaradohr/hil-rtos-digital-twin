#!/bin/bash
for i in $(seq 1 30); do
    sleep 1
    URL=$(journalctl -u magi-tunnel.service --no-pager -n 100 2>/dev/null | grep -oE "https://[a-zA-Z0-9-]+\.tunnel-provider\.com" | grep -v "api.tunnel.example.org" | tail -1)
    if [ -n "$URL" ]; then
        echo "$URL" > [HOME_REDACTED]
        echo "[MAGI-TUNNEL] URL capturada: $URL"
        exit 0
    fi
done
echo "TIMEOUT_EXTRACTING_URL" > [HOME_REDACTED]
exit 0
