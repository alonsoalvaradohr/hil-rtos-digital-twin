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

# 1. Configurar seatd con SEATD_VTBOUND=0 y -l debug
sudo_run("rm -rf /etc/systemd/system/seatd.service.d")
sudo_run("mkdir -p /etc/systemd/system/seatd.service.d")
dropin = """[Service]
ExecStart=
ExecStart=/usr/sbin/seatd -g video -l debug
Environment=SEATD_VTBOUND=0
"""
sftp = client.open_sftp()
with sftp.open('/tmp/seatd_vtbound.conf', 'w') as f:
    f.write(dropin)
sftp.close()

sudo_run("mv /tmp/seatd_vtbound.conf /etc/systemd/system/seatd.service.d/override.conf")

# 2. Configurar magi-kiosk.service
kiosk_service = """[Unit]
Description=MAGI Wayland Kiosk Compositor (Core 1 - Interactive)
After=network.target systemd-user-sessions.service magi-ui.service seatd.service
Wants=magi-ui.service seatd.service
Conflicts=getty@tty1.service

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
sudo_run("systemctl daemon-reload")
sudo_run("systemctl restart seatd")
sudo_run("systemctl restart magi-ui magi-kiosk")
print("[+] Esperando 8 segundos para estabilizacion...")
time.sleep(8)

# 3. Comprobar que seatd abrio la sesion y los inputs
sudo_run("systemctl status seatd --no-pager")
sudo_run("systemctl status magi-kiosk --no-pager")
sudo_run("journalctl -u seatd -n 35 --no-pager")
sudo_run("journalctl -u magi-kiosk -n 35 --no-pager")
sudo_run("fuser -v /dev/input/event* /dev/dri/card* || true")

client.close()

