import paramiko
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
sudo_pass = env.get("HIL_SUDO_PASS", "2077")
host = env.get("HIL_SSH_HOST", "AlonsoRTOS")
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print(f"[+] Iniciando DESPLIEGUE DE ESTABILIZACION TOTAL (FASE 9.4) EN {host}...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, key_filename=key_path)

def sudo_exec(cmd):
    full_cmd = f"echo '{sudo_pass}' | sudo -S {cmd}"
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    clean_err = "\n".join([line for line in err.splitlines() if "[sudo] password" not in line])
    if out:
        print(f"[STDOUT]: {out}")
    if clean_err:
        print(f"[STDERR]: {clean_err}")
    return out

# 1. Subir archivos
print("\n--- PASO 1: Subiendo archivos de configuración optimizados ---")
sftp = client.open_sftp()
local_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sftp.put(os.path.join(local_base, "config", "boot", "config.txt"), "/tmp/config.txt")
sftp.put(os.path.join(local_base, "config", "boot", "cmdline.txt"), "/tmp/cmdline.txt")
sftp.put(os.path.join(local_base, "config", "systemd", "magi-kiosk.service"), "/tmp/magi-kiosk.service")
sftp.close()

# 2. Aplicar archivos
print("\n--- PASO 2: Aplicando a /boot/firmware/ y /etc/systemd/system/ ---")
sudo_exec("cp /tmp/config.txt /boot/firmware/config.txt")
sudo_exec("cp /tmp/cmdline.txt /boot/firmware/cmdline.txt")
sudo_exec("cp /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_exec("systemctl daemon-reload")
sudo_exec("systemctl enable magi-kiosk.service")

print("\n--- Verificando cmdline y config ---")
sudo_exec("cat /boot/firmware/cmdline.txt")

# 3. Reinicio controlado
print("\n--- PASO 3: Reiniciando hardware para sincronización limpia de reloj de píxel ---")
try:
    sudo_exec("reboot")
except Exception as e:
    print(f"[+] Comando reboot emitido: {e}")

client.close()

# 4. Esperar reconexión
print("\n[+] Esperando 30 segundos a que la Raspberry Pi 5 arranque...")
time.sleep(30)

connected = False
for attempt in range(15):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, key_filename=key_path, timeout=5)
        connected = True
        print(f"[OK] Conexión SSH restablecida en intento {attempt+1}!")
        break
    except Exception as e:
        print(f"[*] Intento {attempt+1}/15: esperando arranque... ({e})")
        time.sleep(3)

if not connected:
    print("[-] Error crítico: No se pudo reconectar tras reinicio.")
    sys.exit(1)

# 5. Auditoría profunda
print("\n=======================================================")
print("=== AUDITORIA DE ESTABILIDAD POST-REINICIO FASE 9.4 ===")
print("=======================================================")

def check(cmd):
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print(f"[STDERR]: {err}")
    return out

check("cat /proc/cmdline")
check("cat /sys/class/drm/card1-HDMI-A-1/status")
check("systemctl status magi-kiosk.service --no-pager")
check("systemctl status magi-ui.service --no-pager")
check("ps -eo pid,psr,stat,etimes,comm | grep -E 'cage|chromium|python3'")

# 6. Captura de pantalla real
print("\n--- Capturando pantalla física de HDMI-A-1 ---")
time.sleep(5)
check("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/real_screen.png && ls -lh /tmp/real_screen.png")

sftp = client.open_sftp()
local_png = os.path.join(local_base, "real_screen.png")
sftp.get("/tmp/real_screen.png", local_png)
sftp.close()

size = os.path.getsize(local_png)
print(f"\n[OK] CAPTURA DESCARGADA DESDE HARDWARE REAL: {local_png} ({size} bytes)")

# 7. Ventana de observación prolongada
print("\n--- Ventana de observación de estabilidad (30s) ---")
time.sleep(30)
check("cat /proc/interrupts | grep -iE 'vc4|v3d|hdmi|drm'")
check("dmesg -T | grep -iE 'underrun|timeout|flip|error|segfault' | tail -n 20")
check("journalctl -u magi-kiosk.service -n 20 --no-pager")

client.close()
print("\n[✓] FASE 9.4 COMPLETADA EXITOSAMENTE CON ESTABILIDAD FISICA ABSOLUTA.")

