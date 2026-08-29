import paramiko
import os
import sys
import time

# Cargar variables de entorno locales de forma segura
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
sudo_pass = env.get("HIL_SUDO_PASS", "2077")
host = env.get("HIL_SSH_HOST", "AlonsoRTOS")
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print(f"[+] Iniciando APLICACION DE PARCHE DRM Y REINICIO CONTROLADO EN {host}...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, key_filename=key_path)

def sudo_exec(cmd):
    full_cmd = f"echo '{sudo_pass}' | sudo -S {cmd}"
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    # Filtrar prompt de sudo
    clean_err = "\n".join([line for line in err.splitlines() if "[sudo] password" not in line])
    if out:
        print(f"[STDOUT]: {out}")
    if clean_err:
        print(f"[STDERR]: {clean_err}")
    return out

# 1. Probar sudo
print("\n--- PASO 1: Verificando acceso sudo ---")
sudo_exec("id")

# 2. Subir archivos actualizados a /tmp/
print("\n--- PASO 2: Transfiriendo archivos de configuración canónicos ---")
sftp = client.open_sftp()
local_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sftp.put(os.path.join(local_base, "config", "boot", "cmdline.txt"), "/tmp/cmdline.txt")
sftp.put(os.path.join(local_base, "config", "systemd", "magi-kiosk.service"), "/tmp/magi-kiosk.service")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "templates", "index.html"), "/home/alonso/hil_workstation/05_hmi_display/templates/index.html")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "magi_server.py"), "/home/alonso/hil_workstation/05_hmi_display/magi_server.py")
sftp.close()
print("[+] Archivos transferidos exitosamente a /tmp/")

# 3. Aplicar cmdline.txt y magi-kiosk.service con privilegios root
print("\n--- PASO 3: Inyectando forzado de hardware en /boot/firmware/cmdline.txt ---")
sudo_exec("cp /tmp/cmdline.txt /boot/firmware/cmdline.txt")
sudo_exec("cat /boot/firmware/cmdline.txt")

print("\n--- PASO 4: Inyectando magi-kiosk.service en /etc/systemd/system/ ---")
sudo_exec("cp /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_exec("systemctl daemon-reload")
sudo_exec("systemctl enable magi-kiosk.service")

# 4. Ejecutar reinicio del sistema
print("\n--- PASO 5: Ejecutando REINICIO DE HARDWARE CONTROLADO (sudo reboot) ---")
try:
    sudo_exec("reboot")
except Exception as e:
    print(f"[+] Comando reboot emitido: {e}")

client.close()

# 5. Esperar reconexión post-reinicio
print("\n[+] Esperando 30 segundos a que la Raspberry Pi 5 reinicie el SoC y cargue el kernel RT...")
time.sleep(30)

print("[+] Reintentando conexión SSH tras reinicio...")
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

# 6. Verificación forense post-reinicio
print("\n=======================================================")
print("=== VERIFICACION FORENSE POST-REINICIO DE HARDWARE ===")
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
check("cat /sys/class/drm/card1-HDMI-A-1/modes | head -n 5")
check("systemctl status magi-kiosk.service --no-pager")
check("systemctl status magi-ui.service --no-pager")
check("ps -eo pid,psr,stat,etimes,comm | grep -E 'cage|chromium|python3'")

# 7. Captura de pantalla pericial del conector real HDMI
print("\n--- PASO 7: Capturando fotograma REAL de HDMI-A-1 con grim ---")
time.sleep(5)
check("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/real_screen.png && ls -lh /tmp/real_screen.png")

# 8. Descargar captura al host
sftp = client.open_sftp()
local_png = os.path.join(local_base, "real_screen.png")
sftp.get("/tmp/real_screen.png", local_png)
sftp.close()

size = os.path.getsize(local_png)
print(f"\n[OK] CAPTURA DE PANTALLA REAL DESCARGADA: {local_png} ({size} bytes)")

client.close()
print("\n[✓] TRIAJE DE HARDWARE Y RESTAURACION DRM COMPLETADA EXITOSAMENTE.")

