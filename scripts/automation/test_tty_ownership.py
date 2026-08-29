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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("AlonsoRTOS", port=22, username=user, key_filename=key_path, timeout=5)

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f"\n=======================================================")
    print(f">>> SUDO: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(full, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

# 1. Agregar alonso al grupo tty
sudo_run("usermod -aG tty,input,video,render alonso")
sudo_run("id alonso")

# 2. Configurar magi-kiosk.service con gestion completa de VT y grupos
svc_content = """[Unit]
Description=MAGI Wayland Kiosk Compositor (Core 1 - Interactive)
After=network.target systemd-user-sessions.service magi-ui.service seatd.service
Wants=magi-ui.service seatd.service
Conflicts=user-host

[Service]
User=alonso
Group=alonso
SupplementaryGroups=video input render tty dialout bluetooth
PAMName=login
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
StandardInput=tty-fail
StandardOutput=journal
StandardError=journal
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WLR_BACKENDS=drm
Environment=WLR_RENDERER=gles2
Environment=WLR_NO_HARDWARE_CURSORS=1
Environment=LIBSEAT_BACKEND=seatd
Environment=XDG_SESSION_TYPE=wayland
Environment=WAYLAND_DEBUG=1
ExecStart=/usr/bin/cage -s -- /usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --remote-debugging-port=9222 --use-fake-ui-for-media-stream --unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080 --ozone-platform=wayland --enable-features=OverlayScrollbar,TouchTextSelection --touch-events=enabled --enable-touch-drag-drop --disable-translate --disable-features=Translate,OptimizationHints --window-size=1024,600 --window-position=0,0 http://127.0.0.1:8080/
Restart=always
RestartSec=2s
CPUAffinity=1

[Install]
WantedBy=graphical.target
"""

sftp = client.open_sftp()
with sftp.open('/tmp/magi-kiosk.service', 'w') as f:
    f.write(svc_content)
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("systemctl daemon-reload && systemctl restart seatd magi-ui magi-kiosk")
time.sleep(6)

# 3. Verificar que procesos abrieron los dispositivos de entrada ahora
sudo_run("fuser -v /dev/input/event* /dev/dri/card* /run/seatd.sock || true")

client.close()
