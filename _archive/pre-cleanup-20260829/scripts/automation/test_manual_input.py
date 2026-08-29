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
    print(f">>> SUDO: {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

def user_run(cmd):
    print(f">>> USER: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)
    return out

# 1. Detener el servicio kiosk
sudo_run("systemctl stop magi-kiosk")

# 2. Ejecutar cage con WLR_LOG_LEVEL=debug en segundo plano durante 6 segundos
user_run("""
XDG_RUNTIME_DIR=/run/user/1000 \
WLR_BACKENDS=drm \
WLR_RENDERER=gles2 \
WLR_LOG_LEVEL=debug \
LIBSEAT_BACKEND=seatd \
WLR_NO_HARDWARE_CURSORS=1 \
timeout 5 cage -s -- true > /tmp/cage_debug.log 2>&1 || true
""")

sudo_run("systemctl restart magi-kiosk")
user_run("sleep 5")

sudo_run("fuser -v /dev/input/event* /dev/dri/card* /run/seatd.sock || true")
sudo_run("lsof /dev/input/event* || true")
sudo_run("cat /proc/bus/input/devices")

client.close()
