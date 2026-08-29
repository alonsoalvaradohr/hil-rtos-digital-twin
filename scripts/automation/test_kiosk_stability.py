import os
import sys
import time
import paramiko

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))
sudo_pass = env.get("HIL_SUDO_PASS", "2077")

hosts = ["AlonsoRTOS", "192.168.4.2", "192.168.100.30"]

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def get_client():
    for h in hosts:
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(h, port=22, username=user, key_filename=key_path, timeout=4)
            return c
        except Exception:
            pass
    raise RuntimeError("No se pudo conectar")

client = get_client()

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f"\n=======================================================")
    print(f">>> SUDO: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(full, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    return out

# 1. Purgar perfiles antiguos de Chromium
sudo_run("rm -rf /tmp/chromium_magi_profile")

# 2. Configurar magi-kiosk.service sin dependencias tty fragiles
kiosk_service = """[Unit]
Description=MAGI Wayland Kiosk Compositor (Core 1 - Interactive)
After=network.target systemd-user-sessions.service magi-ui.service seatd.service
Wants=magi-ui.service seatd.service

[Service]
User=alonso
Group=alonso
SupplementaryGroups=video input render tty dialout bluetooth
StandardInput=null
StandardOutput=journal
StandardError=journal
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WLR_BACKENDS=drm
Environment=WLR_RENDERER=gles2
Environment=LIBSEAT_BACKEND=seatd
Environment=SEATD_VTBOUND=0
Environment=XDG_SESSION_TYPE=wayland
Environment=XCURSOR_SIZE=24
Environment=XCURSOR_THEME=Adwaita
ExecStart=/usr/bin/cage -s -- /usr/bin/chromium-browser --kiosk --app=http://127.0.0.1:8080/ --noerrdialogs --disable-infobars --no-first-run --no-default-browser-check --disable-session-crashed-bubble --remote-debugging-port=9222 --use-fake-ui-for-media-stream --unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080 --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection --touch-events=enabled --disable-pinch --overscroll-history-navigation=0 --disable-translate --disable-features=Translate,OptimizationHints --user-data-dir=/tmp/chromium_magi_profile --window-size=1024,600 --window-position=0,0
Restart=always
RestartSec=2s
CPUAffinity=1

[Install]
WantedBy=graphical.target
"""

sftp = client.open_sftp()
with sftp.open('/tmp/magi-kiosk.service', 'w') as f:
    f.write(kiosk_service)
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("systemctl daemon-reload && systemctl restart magi-kiosk")

print("[+] Esperando 20 segundos para verificar estabilidad continua...")
time.sleep(20)

sudo_run("systemctl status magi-kiosk --no-pager")
sudo_run("journalctl -u magi-kiosk -n 25 --no-pager")

client.close()
