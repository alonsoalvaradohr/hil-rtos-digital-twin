#!/bin/bash
for i in $(seq 1 30); do
    sleep 1
    URL=$(journalctl -u magi-tunnel.service --no-pager -n 100 2>/dev/null | grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" | grep -v "api.trycloudflare.com" | tail -1)
    if [ -n "$URL" ]; then
        echo "$URL" > /home/alonso/magi_url.txt
        echo "[MAGI-TUNNEL] URL capturada: $URL"
        exit 0
    fi
done
echo "TIMEOUT_EXTRACTING_URL" > /home/alonso/magi_url.txt
exit 0
