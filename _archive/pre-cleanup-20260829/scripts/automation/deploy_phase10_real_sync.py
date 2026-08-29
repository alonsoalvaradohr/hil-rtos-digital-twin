import os
import sys
import time
import paramiko

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
sudo_pass = env.get("HIL_SUDO_PASS", "2077")
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))
hosts = [env.get("HIL_SSH_HOST", "192.168.100.30"), "192.168.100.30", "AlonsoRTOS", "192.168.4.2"]

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] INICIANDO DESPLIEGUE FÍSICO REAL, PURGA Y SINCRONIZACION (FASE 10.1) EN RASPBERRY PI 5...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

connected = False
for attempt in range(6):
    for h in ["192.168.100.30", "192.168.4.2"]:
        try:
            print(f"[+] Intento {attempt+1}: Conectando a {h}:22...")
            client.connect(h, port=22, username=user, key_filename=key_path, timeout=8)
            print(f"[OK] Conectado exitosamente a {h}")
            connected = True
            break
        except Exception as e:
            print(f"[*] Falló conexión a {h}: {e}")
    if connected:
        break
    time.sleep(2)

if not connected:
    print("[-] Error crítico: No se pudo conectar a la Raspberry Pi.")
    sys.exit(1)

def run(cmd, use_sudo=False):
    full_cmd = f"echo '{sudo_pass}' | sudo -S {cmd}" if use_sudo else cmd
    print(f">>> {full_cmd}")
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=40)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err and 'password for alonso' not in err and '[sudo]' not in err:
        print("[STDERR]:", err)
    return out

# 1. Purga total de procesos colgados y archivos temporales
print("\n--- PASO 1 (AGENT-CLEANER): Purga de procesos colgados y archivos temporales ---")
run('pkill -9 -f cage || true', use_sudo=True)
run('pkill -9 -f chromium || true', use_sudo=True)
run('rm -rf /tmp/chromium_kiosk /run/user/1000/wayland-* /tmp/magi_screen*.png /tmp/real_screen*.png', use_sudo=True)

# 2. Sincronizar código fuente puro y limpio
print("\n--- PASO 2 (AGENT-DEPLOYER): Sincronizando frontend limpio y magi_server.py ---")
remote_base = '[HOME_REDACTED]'
run(f'mkdir -p {remote_base}/static/css {remote_base}/static/js {remote_base}/templates')

local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
local_base = os.path.join(local_root, 'src', 'hmi_ui')

sftp = client.open_sftp()
sftp.put(os.path.join(local_base, 'magi_server.py'), f'{remote_base}/magi_server.py')
sftp.put(os.path.join(local_base, 'templates', 'index.html'), f'{remote_base}/templates/index.html')
sftp.put(os.path.join(local_base, 'static', 'css', 'magi.css'), f'{remote_base}/static/css/magi.css')
sftp.put(os.path.join(local_base, 'static', 'js', 'magi.js'), f'{remote_base}/static/js/magi.js')
sftp.put(os.path.join(local_base, 'static', 'js', 'network.js'), f'{remote_base}/static/js/network.js')
sftp.put(os.path.join(local_base, 'static', 'js', 'keyboard.js'), f'{remote_base}/static/js/keyboard.js')

# Subir magi-kiosk.service corregido (sin WLR_LIBINPUT_NO_DEVICES)
local_service = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
sftp.put(local_service, '/tmp/magi-kiosk.service')
sftp.close()

run('mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service', use_sudo=True)
run('chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service', use_sudo=True)

# 3. Recargar y arrancar servicios en Core 1
print("\n--- PASO 3 (AGENT-EXECUTOR): Recargando daemons y arrancando servicios ---")
run('systemctl daemon-reload', use_sudo=True)
run('systemctl restart seatd magi-ui magi-kiosk', use_sudo=True)
time.sleep(6)

# 4. Auditoría y verificación de estado
print("\n=======================================================")
print("=== AUDITORIA Y CERTIFICACION DE CAMPO FASE 10.1 ===")
print("=======================================================")
run('systemctl status magi-ui.service --no-pager')
run('systemctl status magi-kiosk.service --no-pager')
run('ps -eo pid,psr,stat,comm,args | grep -E "cage|chromium|python3" | grep -v grep')

# 5. Tomar captura pericial real sobre HDMI-A-1
print("\n--- PASO 4 (AGENT-TESTER): Tomando captura pericial física con grim ---")
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] /tmp/magi_screen_live.png')

sftp = client.open_sftp()
os.makedirs(os.path.join(local_root, 'telemetry'), exist_ok=True)
target_local_live = os.path.join(local_root, 'telemetry', 'magi_screen_live.png')
sftp.get('/tmp/magi_screen_live.png', target_local_live)
sftp.close()

print(f"[OK] Captura física descargada: {target_local_live} ({os.path.getsize(target_local_live)} bytes)")
print("[OK] Sincronización física, purga y arranque táctil completados con éxito.")
client.close()
