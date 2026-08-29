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
    raise RuntimeError("No se pudo conectar a la Raspberry Pi")

client = get_client()
print("[OK] Conectado exitosamente al silicio de la Raspberry Pi")

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f"\n=======================================================")
    print(f">>> SUDO: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(full, timeout=35)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

def user_run(cmd):
    print(f"\n=======================================================")
    print(f">>> USER: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=35)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)
    return out

local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Purgar sockets y temporales obsoletos
print("\n--- PASO 1: Purga de sockets Wayland obsoletos y caches ---")
sudo_run("systemctl stop magi-kiosk seatd || true")
sudo_run("rm -f /run/user/1000/wayland-* /run/seatd.sock /tmp/chromium_kiosk/* || true")

# 2. Desplegar reglas udev canónicas
print("\n--- PASO 2: Despliegue de Reglas Udev para Seat0 y Uaccess ---")
local_udev = os.path.join(local_root, 'Digital_Twin_Workspace', 'etc', 'udev', 'rules.d', '99-magi-touch-input.rules')
sftp = client.open_sftp()
sftp.put(local_udev, '/tmp/99-magi-touch-input.rules')
sftp.close()

sudo_run("mv /tmp/99-magi-touch-input.rules /etc/udev/rules.d/99-magi-touch-input.rules")
sudo_run("chown root:root /etc/udev/rules.d/99-magi-touch-input.rules && chmod 644 /etc/udev/rules.d/99-magi-touch-input.rules")
sudo_run("udevadm control --reload && udevadm trigger")

# 3. Desplegar override de seatd (SEATD_VTBOUND=0 y /usr/sbin/seatd)
print("\n--- PASO 3: Despliegue de Override para seatd (SEATD_VTBOUND=0) ---")
sudo_run("mkdir -p /etc/systemd/system/seatd.service.d")
dropin = """[Service]
ExecStart=
ExecStart=/usr/sbin/seatd -g video -l debug
Environment=SEATD_VTBOUND=0
"""
sftp = client.open_sftp()
with sftp.open('/tmp/seatd_override.conf', 'w') as f:
    f.write(dropin)
sftp.close()
sudo_run("mv /tmp/seatd_override.conf /etc/systemd/system/seatd.service.d/override.conf")

# 4. Desplegar magi-kiosk.service canonico
print("\n--- PASO 4: Despliegue de magi-kiosk.service Canónico ---")
local_svc = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
sftp = client.open_sftp()
sftp.put(local_svc, '/tmp/magi-kiosk.service')
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service")

# 5. Sincronizar Frontend
print("\n--- PASO 5: Sincronizacion de Assets Frontend ---")
local_hmi = os.path.join(local_root, 'src', 'hmi_ui')
remote_hmi = '/home/alonso/hil_workstation/05_hmi_display'

def transfer_file(local_file, remote_file):
    with open(local_file, 'rb') as f:
        content = f.read()
    sftp = client.open_sftp()
    with sftp.open(remote_file, 'wb') as rf:
        rf.write(content)
    sftp.close()

transfer_file(os.path.join(local_hmi, 'magi_server.py'), f'{remote_hmi}/magi_server.py')
transfer_file(os.path.join(local_hmi, 'templates', 'index.html'), f'{remote_hmi}/templates/index.html')
transfer_file(os.path.join(local_hmi, 'static', 'css', 'magi.css'), f'{remote_hmi}/static/css/magi.css')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'magi.js'), f'{remote_hmi}/static/js/magi.js')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'network.js'), f'{remote_hmi}/static/js/network.js')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'keyboard.js'), f'{remote_hmi}/static/js/keyboard.js')

# 6. Reiniciar y estabilizar cadena de servicios
print("\n--- PASO 6: Reinicio e Inicializacion de Daemons ---")
sudo_run("systemctl daemon-reload")
sudo_run("systemctl restart seatd")
sudo_run("systemctl restart magi-ui magi-kiosk")
print("[+] Esperando 8 segundos a que Cage y Chromium se estabilicen...")
time.sleep(8)

# 7. Diagnóstico forense en vivo
print("\n--- PASO 7: Auditoria de Procesos y Descriptores ---")
sudo_run("systemctl status seatd --no-pager")
sudo_run("systemctl status magi-kiosk --no-pager")
sudo_run("udevadm info /dev/input/event0 | grep -iE 'seat|tag|uaccess'")
sudo_run("udevadm info /dev/input/event1 | grep -iE 'seat|tag|uaccess'")
user_run("ps -eo pid,psr,stat,comm,args | grep -E 'cage|chromium|python3' | grep -v grep")

# 8. Captura de Framebuffer Fisico
print("\n--- PASO 8: Captura Pericial del Framebuffer Fisico ---")
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/magi_screen_live.png")

telemetry_dir = os.path.join(local_root, 'telemetry')
os.makedirs(telemetry_dir, exist_ok=True)
sftp = client.open_sftp()
sftp.get('/tmp/magi_screen_live.png', os.path.join(telemetry_dir, 'magi_screen_live.png'))
sftp.close()
print("[OK] Captura descargada a telemetry/magi_screen_live.png")

client.close()
print("\n[✓] DESPLIEGUE Y CERTIFICACION CANONICA FASE 11.1 COMPLETADA.")

