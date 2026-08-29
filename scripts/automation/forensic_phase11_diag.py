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

def user_run(cmd):
    print(f"\n=======================================================")
    print(f">>> USER: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)
    return out

# 1. Configurar seatd con logging de depuracion maximo
seatd_dropin_dir = "/etc/systemd/system/seatd.service.d"
sudo_run(f"mkdir -p {seatd_dropin_dir}")
dropin_content = """[Service]
ExecStart=
ExecStart=/usr/bin/seatd -g video -u debug
"""
sftp = client.open_sftp()
with sftp.open('/tmp/seatd_debug.conf', 'w') as f:
    f.write(dropin_content)
sftp.close()

sudo_run(f"mv /tmp/seatd_debug.conf {seatd_dropin_dir}/debug.conf")
sudo_run("systemctl daemon-reload && systemctl restart seatd")

# 2. Configurar magi-kiosk con WLR_LOG_LEVEL=debug y WAYLAND_DEBUG=1
kiosk_service = """[Unit]
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
Environment=WLR_LOG_LEVEL=debug
Environment=LIBSEAT_BACKEND=seatd
Environment=XDG_SESSION_TYPE=wayland
Environment=XCURSOR_SIZE=24
Environment=XCURSOR_THEME=Adwaita
ExecStart=/usr/bin/cage -s -- /usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --remote-debugging-port=9222 --use-fake-ui-for-media-stream --unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080 --ozone-platform=wayland --enable-features=OverlayScrollbar,TouchTextSelection --touch-events=enabled --enable-touch-drag-drop --disable-translate --disable-features=Translate,OptimizationHints --window-size=1024,600 --window-position=0,0 http://127.0.0.1:8080/
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
time.sleep(6)

# 3. Leer logs de seatd y cage para verificar apertura de dispositivos
sudo_run("journalctl -u seatd -n 40 --no-pager")
sudo_run("journalctl -u magi-kiosk -n 60 --no-pager")

client.close()
