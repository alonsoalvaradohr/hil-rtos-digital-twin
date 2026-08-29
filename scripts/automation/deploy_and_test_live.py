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
host = "192.168.100.30"

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print(f"[+] CONECTANDO AL SILICIO VIVO EN {host}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=22, username=user, key_filename=key_path, timeout=8)

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

# 1. Transferencia atómica de archivos
print("\n--- PASO 1: Transferencia de código y configuraciones limpias ---")
local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
local_hmi = os.path.join(local_root, 'src', 'hmi_ui')
remote_hmi = '/home/alonso/hil_workstation/05_hmi_display'

sftp = client.open_sftp()
sftp.put(os.path.join(local_hmi, 'magi_server.py'), f'{remote_hmi}/magi_server.py')
sftp.put(os.path.join(local_hmi, 'templates', 'index.html'), f'{remote_hmi}/templates/index.html')
sftp.put(os.path.join(local_hmi, 'static', 'css', 'magi.css'), f'{remote_hmi}/static/css/magi.css')
sftp.put(os.path.join(local_hmi, 'static', 'js', 'magi.js'), f'{remote_hmi}/static/js/magi.js')
sftp.put(os.path.join(local_hmi, 'static', 'js', 'network.js'), f'{remote_hmi}/static/js/network.js')
sftp.put(os.path.join(local_hmi, 'static', 'js', 'keyboard.js'), f'{remote_hmi}/static/js/keyboard.js')

local_svc = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
sftp.put(local_svc, '/tmp/magi-kiosk.service')
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service")

# 2. Recargar servicios
print("\n--- PASO 2: Recarga e inicialización de daemons ---")
sudo_run("systemctl daemon-reload")
sudo_run("systemctl restart seatd magi-ui magi-kiosk")
print("[+] Esperando 8 segundos para estabilización completa de render...")
time.sleep(8)

# 3. Auditoría de procesos
print("\n--- PASO 3: Verificación de procesos en ejecución ---")
user_run("ps -eo pid,psr,stat,comm,args | grep -E 'cage|chromium|python3' | grep -v grep")
user_run("systemctl status magi-kiosk.service --no-pager")

# 4. Captura inicial del framebuffer
print("\n--- PASO 4: Captura visual del estado inicial ---")
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/screen_live_01.png")

sftp = client.open_sftp()
os.makedirs(os.path.join(local_root, 'telemetry'), exist_ok=True)
sftp.get('/tmp/screen_live_01.png', os.path.join(local_root, 'telemetry', 'magi_screen_live.png'))
sftp.close()
print("[OK] Captura inicial descargada a telemetry/magi_screen_live.png")

client.close()
print("\n[OK] DESPLIEGUE Y CERTIFICACION DE SERVICIOS COMPLETADA.")

