import os
import sys
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
    stdin, stdout, stderr = client.exec_command(full, timeout=25)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

def user_run(cmd):
    print(f"\n=======================================================")
    print(f">>> USER: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=25)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)
    return out

# 1. Detener y deshabilitar magi-kiosk.service
print("\n--- PASO 1: Deteniendo y deshabilitando magi-kiosk.service ---")
sudo_run("systemctl stop magi-kiosk.service")
sudo_run("systemctl disable magi-kiosk.service")

# 2. Asegurar que magi-ui.service (servidor HTTP backend) esté activo
print("\n--- PASO 2: Verificando backend HTTP (magi-ui.service) ---")
sudo_run("systemctl restart magi-ui.service")
sudo_run("systemctl status magi-ui.service --no-pager")

# 3. Crear script ejecutable local ~/start_kiosk_local.sh
print("\n--- PASO 3: Creando script local ~/start_kiosk_local.sh ---")
launcher_content = """#!/bin/bash
# Script de Lanzamiento Local Directo en Consola Fisica tty1
echo "=== INICIANDO ENTORNO GRAFICO LOCAL LABWC / CHROMIUM ==="
rm -rf /tmp/chromium_magi_profile/Singleton* /run/user/1000/wayland-* 2>/dev/null || true

export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export WLR_BACKENDS=drm
export WLR_RENDERER=gles2
export XCURSOR_THEME=Adwaita
export XCURSOR_SIZE=24

exec labwc -s "/usr/bin/chromium-browser --no-sandbox --disable-setuid-sandbox --kiosk --noerrdialogs --disable-infobars --no-first-run --no-default-browser-check --disable-session-crashed-bubble --disable-extensions --disable-background-networking --disable-sync --disable-translate --metrics-recording-only --no-service-autorun --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection --touch-events=enabled --disable-pinch --user-data-dir=/tmp/chromium_magi_profile http://127.0.0.1:8080/"
"""

sftp = client.open_sftp()
with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(launcher_content)
sftp.close()

user_run("chmod +x [HOME_REDACTED]")
print("[OK] Script ~/start_kiosk_local.sh listo para ejecución en consola física.")

client.close()
