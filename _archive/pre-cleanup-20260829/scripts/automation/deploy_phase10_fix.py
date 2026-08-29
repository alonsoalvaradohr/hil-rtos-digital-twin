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

hosts_to_try = [env.get("HIL_SSH_HOST", "192.168.100.30"), "192.168.100.30", "AlonsoRTOS", "192.168.4.2"]
connected = False
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for h in hosts_to_try:
    try:
        print(f"[+] Conectando a {h}...")
        client.connect(h, username=user, key_filename=key_path, timeout=6)
        print(f"[OK] Conectado exitosamente a {h}")
        connected = True
        break
    except Exception as e:
        print(f"[*] Falló conexión a {h}: {e}")

if not connected:
    print("[-] Error crítico: No se pudo conectar a la Raspberry Pi.")
    sys.exit(1)

def sudo_exec(cmd):
    full_cmd = f"echo '{sudo_pass}' | sudo -S {cmd}"
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    clean_err = "\n".join([line for line in err.splitlines() if "[sudo] password" not in line and line.strip()])
    if out:
        print(f"[STDOUT]: {out}")
    if clean_err:
        print(f"[STDERR]: {clean_err}")
    return out

# 1. Purga remota de archivos temporales
print("\n--- PASO 1 (AGENT-CLEANER): Purga remota de archivos temporales en /tmp ---")
sudo_exec("rm -rf /tmp/org.chromium.* /tmp/*.png /tmp/*.service /tmp/*.txt /tmp/config.txt /tmp/cmdline.txt")

# 2. Subir configuraciones y archivos UI
print("\n--- PASO 2 (AGENT-DEPLOYER): Sincronizando archivos UI y servicio Wayland Kiosk ---")
sftp = client.open_sftp()
local_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Subir magi-kiosk.service
sftp.put(os.path.join(local_base, "config", "systemd", "magi-kiosk.service"), "/tmp/magi-kiosk.service")
sftp.put(os.path.join(local_base, "config", "boot", "config.txt"), "/tmp/config.txt")
sftp.put(os.path.join(local_base, "config", "boot", "cmdline.txt"), "/tmp/cmdline.txt")

# Sincronizar frontend UI en hil_workstation/05_hmi_display
remote_hmi = "[HOME_REDACTED]"
sftp.put(os.path.join(local_base, "src", "hmi_ui", "magi_server.py"), f"{remote_hmi}/magi_server.py")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "templates", "index.html"), f"{remote_hmi}/templates/index.html")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "static", "css", "magi.css"), f"{remote_hmi}/static/css/magi.css")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "static", "js", "magi.js"), f"{remote_hmi}/static/js/magi.js")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "static", "js", "network.js"), f"{remote_hmi}/static/js/network.js")
sftp.put(os.path.join(local_base, "src", "hmi_ui", "static", "js", "keyboard.js"), f"{remote_hmi}/static/js/keyboard.js")

sftp.close()

# 3. Aplicar configuraciones
print("\n--- PASO 3 (AGENT-EXECUTOR): Aplicando servicio magi-kiosk y reiniciando HMI ---")
sudo_exec("cp /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_exec("cp /tmp/config.txt /boot/firmware/config.txt")
sudo_exec("cp /tmp/cmdline.txt /boot/firmware/cmdline.txt")
sudo_exec("systemctl daemon-reload")
sudo_exec("systemctl restart magi-ui.service")
sudo_exec("systemctl restart magi-kiosk.service")

print("\n--- Esperando 5 segundos para estabilización de render Wayland ---")
time.sleep(5)

# 4. Captura y verificación de estado
print("\n=======================================================")
print("=== AUDITORIA Y VERIFICACION DE ESTABILIDAD FASE 10 ===")
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

check("systemctl status magi-ui.service --no-pager")
check("systemctl status magi-kiosk.service --no-pager")
check("ps -eo pid,psr,stat,comm,args | grep -E 'cage|chromium|python3'")
check("journalctl -u magi-kiosk -n 25 --no-pager")

# Capturar frame de pantalla con grim
print("\n--- Capturando pantalla con grim para certificación visual ---")
client.exec_command("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] /tmp/real_screen.png")
time.sleep(1)

# Descargar captura
sftp = client.open_sftp()
os.makedirs(os.path.join(local_base, "telemetry"), exist_ok=True)
local_screenshot = os.path.join(local_base, "telemetry", "real_screen.png")
sftp.get("/tmp/real_screen.png", local_screenshot)
sftp.close()
print(f"[✓] Captura descargada con éxito a {local_screenshot} ({os.path.getsize(local_screenshot)} bytes)")

client.close()
print("\n[✓] DESPLIEGUE, SINCRONIZACION Y CERTIFICACION FASE 10.0 COMPLETADOS.")
