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
    raise RuntimeError("No se pudo conectar a la Raspberry Pi 5")

client = get_client()
print("[OK] Conectado exitosamente a la Raspberry Pi 5")

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

# 1. Desplegar magi-kiosk.service con --no-sandbox y --disable-setuid-sandbox
print("\n--- PASO 1: Despliegue de magi-kiosk.service con No-Sandbox ---")
local_svc = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
sftp = client.open_sftp()
sftp.put(local_svc, '/tmp/magi-kiosk.service')
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service")

# 2. Purgar bloqueos de Singleton previos
print("\n--- PASO 2: Purga de SingletonLock y Temporales ---")
sudo_run("rm -rf /tmp/chromium_magi_profile/Singleton* /tmp/chromium_magi_profile/lockfile || true")

# 3. Recargar systemd y reiniciar servicio
print("\n--- PASO 3: Recarga y Reinicio del Servicio Kiosko ---")
sudo_run("systemctl daemon-reload")
sudo_run("systemctl restart magi-kiosk.service")

print("[+] Esperando 8 segundos para estabilización...")
time.sleep(8)

# 4. Verificar estados y procesos activos
print("\n--- PASO 4: Auditoría de Procesos ---")
sudo_run("systemctl status magi-kiosk.service --no-pager")
user_run("ps -eo pid,psr,stat,comm,args | grep -E 'labwc|chromium' | grep -v grep")

# 5. Captura Pericial del Framebuffer Físico
print("\n--- PASO 5: Captura Pericial del Framebuffer Físico ---")
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] /tmp/magi_screen_nosandbox.png")

telemetry_dir = os.path.join(local_root, 'telemetry')
os.makedirs(telemetry_dir, exist_ok=True)
sftp = client.open_sftp()
sftp.get('/tmp/magi_screen_nosandbox.png', os.path.join(telemetry_dir, 'magi_screen_nosandbox.png'))
sftp.close()
print("[OK] Captura guardada en telemetry/magi_screen_nosandbox.png")

client.close()
print("\n[✓] FASE 15.0: DESACTIVACIÓN DE SANDBOX Y DESPLIEGUE COMPLETADO.")

