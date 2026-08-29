import paramiko
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
host = env.get('HIL_SSH_HOST', 'AlonsoRTOS')
user = env.get('HIL_SSH_USER', 'alonso')
key_path = os.path.expanduser(env.get('HIL_SSH_KEY_PATH', '~/.ssh/id_ed25519_hil'))

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, key_filename=key_path)

def run(cmd):
    print("\n>>> " + cmd)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print("[STDERR]:", err)
    return out

# 1. Inspeccionar salidas reales en Wayland
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/wlr-randr')

# 2. Tomar captura de pantalla física con grim
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/real_screen.png && ls -lh /tmp/real_screen.png')

# 3. Descargar captura al host
sftp = client.open_sftp()
local_png = 'E:/alons/Documents/Raspberry HIL/real_screen.png'
sftp.get('/tmp/real_screen.png', local_png)
sftp.close()

size = os.path.getsize(local_png)
print(f"\n[OK] CAPTURA DESCARGADA DESDE HARDWARE REAL: {local_png} ({size} bytes)")

# 4. Verificar estado y afinidad de procesos
run('ps -eo pid,psr,stat,etimes,comm | grep -E "cage|chromium|python3" | grep -v grep')

# 5. Verificar estado de servicio magi-kiosk
run('systemctl status magi-kiosk.service --no-pager')

client.close()

