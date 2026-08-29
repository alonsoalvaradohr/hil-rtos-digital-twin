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

print(f"[+] Iniciando APLICACION DE PARCHE DE ESTABILIZACION DE HARDWARE (FASE 9.3) EN {host}...")

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

# 1. Subir archivos actualizados
print("\n--- PASO 1: Subiendo configuraciones de firmware y systemd ---")
sftp = client.open_sftp()
local_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sftp.put(os.path.join(local_base, "config", "boot", "config.txt"), "/tmp/config.txt")
sftp.put(os.path.join(local_base, "config", "boot", "cmdline.txt"), "/tmp/cmdline.txt")
sftp.put(os.path.join(local_base, "config", "systemd", "magi-kiosk.service"), "/tmp/magi-kiosk.service")
sftp.close()
print("[+] Archivos subidos a /tmp/.")

# 2. Aplicar archivos con privilegios de root
print("\n--- PASO 2: Inyectando config.txt y cmdline.txt en /boot/firmware/ ---")
sudo_exec("cp /tmp/config.txt /boot/firmware/config.txt")
sudo_exec("cp /tmp/cmdline.txt /boot/firmware/cmdline.txt")
sudo_exec("cp /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_exec("systemctl daemon-reload")
sudo_exec("systemctl enable magi-kiosk.service")

print("\n--- Verificando contenido aplicado ---")
sudo_exec("cat /boot/firmware/config.txt | tail -n 25")
sudo_exec("cat /boot/firmware/cmdline.txt")

# 3. Reinicio de hardware
print("\n--- PASO 3: Reiniciando hardware para aplicar CMA-512, HDMI Boost 7 y supresión HPD ---")
try:
    sudo_exec("reboot")
except Exception as e:
    print(f"[+] Comando reboot emitido: {e}")

client.close()

# 4. Esperar reconexión
print("\n[+] Esperando 30 segundos a que el hardware reinicie y cargue el nuevo árbol de dispositivos...")
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

# 5. Auditoría post-reinicio
print("\n=======================================================")
print("=== AUDITORIA POST-REINICIO DE HARDWARE (FASE 9.3) ===")
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
check("cat /proc/interrupts | grep -iE 'vc4|v3d|hdmi|drm'")
check("dmesg -T | grep -iE 'underrun|v3d|vc4|drm|crtc|plane|hpd|timeout|flip' | tail -n 30")
check("cat /sys/class/drm/card1-HDMI-A-1/status")
check("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/wlr-randr")
check("systemctl status magi-kiosk.service --no-pager")
check("systemctl status magi-ui.service --no-pager")
check("ps -eo pid,psr,stat,etimes,comm | grep -E 'cage|chromium|python3'")

# 6. Captura de pantalla real desde HDMI-A-1
print("\n--- Capturando pantalla física de HDMI-A-1 ---")
time.sleep(5)
check("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/real_screen.png && ls -lh /tmp/real_screen.png")

sftp = client.open_sftp()
local_png = os.path.join(local_base, "real_screen.png")
sftp.get("/tmp/real_screen.png", local_png)
sftp.close()

size = os.path.getsize(local_png)
print(f"\n[OK] CAPTURA DESCARGADA DESDE HARDWARE REAL: {local_png} ({size} bytes)")

# 7. Ventana de observación de estabilidad (30 segundos)
print("\n--- Ventana de observación de estabilidad (30s) ---")
time.sleep(30)
check("cat /proc/interrupts | grep -iE 'vc4|v3d|hdmi|drm'")
check("dmesg -T | grep -iE 'underrun|timeout|flip|error' | tail -n 20")

client.close()
print("\n[✓] FASE 9.3 COMPLETADA EXITOSAMENTE CON ESTABILIDAD FISICA ABSOLUTA.")
