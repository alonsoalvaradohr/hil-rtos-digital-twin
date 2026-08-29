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

# 1. Probar LIBSEAT_BACKEND=builtin
sudo_run("systemctl stop magi-kiosk")
user_run("""
XDG_RUNTIME_DIR=/run/user/1000 \
WLR_BACKENDS=drm \
WLR_RENDERER=gles2 \
WLR_LOG_LEVEL=debug \
LIBSEAT_BACKEND=builtin \
WLR_NO_HARDWARE_CURSORS=1 \
timeout 4 cage -s -- sleep 4 > /tmp/cage_builtin.log 2>&1 || true
""")

user_run("cat /tmp/cage_builtin.log")

# 2. Probar LIBSEAT_BACKEND=logind
user_run("""
XDG_RUNTIME_DIR=/run/user/1000 \
WLR_BACKENDS=drm \
WLR_RENDERER=gles2 \
WLR_LOG_LEVEL=debug \
LIBSEAT_BACKEND=logind \
WLR_NO_HARDWARE_CURSORS=1 \
timeout 4 cage -s -- sleep 4 > /tmp/cage_logind.log 2>&1 || true
""")

user_run("cat /tmp/cage_logind.log")

client.close()

