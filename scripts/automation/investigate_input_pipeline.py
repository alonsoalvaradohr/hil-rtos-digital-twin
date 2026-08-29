import paramiko
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))
sudo_pass = env.get("HIL_SUDO_PASS", "2077")

hosts = ["AlonsoRTOS", "192.168.4.2", "192.168.100.30"]

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = None
for h in hosts:
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(h, port=22, username=user, key_filename=key_path, timeout=5)
        client = c
        print(f"[OK] Conectado a {h}")
        break
    except Exception:
        pass

if not client:
    print("[ERR] No se pudo conectar a la Pi")
    sys.exit(1)

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

def user_run(cmd):
    print(f"\n=======================================================")
    print(f">>> USER: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)

# 1. Sesiones de logind y seatd
sudo_run("loginctl list-sessions; loginctl list-seats; loginctl show-seat seat0")
sudo_run("journalctl -u seatd -n 30 --no-pager")
sudo_run("journalctl -u magi-kiosk -n 40 --no-pager")

# 2. Permisos y sockets
sudo_run("ls -la /run/seatd.sock /dev/tty1 /dev/input/event* /dev/dri/card*")

# 3. Que compositores Wayland estan instalados en la Pi?
user_run("which cage labwc sway wayfire weston mutter kwin_wayland || true")

client.close()
