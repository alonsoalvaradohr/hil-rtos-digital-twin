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

# 1. Crear directorios de configuración de labwc
print("\n--- PASO 1: Creación de estructura de configuración para labwc ---")
user_run("mkdir -p /home/alonso/.config/labwc")

rc_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<labwc_config>
  <core>
    <decoration>none</decoration>
    <gap>0</gap>
  </core>
  <focus>
    <followMouse>yes</followMouse>
    <raiseOnFocus>yes</raiseOnFocus>
  </focus>
  <touch>
    <mapToOutput>HDMI-A-1</mapToOutput>
  </touch>
  <keyboard>
    <repeatRate>25</repeatRate>
    <repeatDelay>500</repeatDelay>
    <default />
  </keyboard>
  <mouse>
    <default />
  </mouse>
  <windowRules>
    <windowRule identifier="*" serverDecoration="no">
      <action name="Maximize"/>
      <action name="Focus"/>
      <action name="Raise"/>
    </windowRule>
  </windowRules>
</labwc_config>
"""

autostart_content = """#!/bin/sh
# Autostart para Labwc Kiosko MAGI
/usr/bin/chromium-browser \\
  --kiosk \\
  --noerrdialogs \\
  --disable-infobars \\
  --no-first-run \\
  --no-default-browser-check \\
  --disable-session-crashed-bubble \\
  --remote-debugging-port=9222 \\
  --use-fake-ui-for-media-stream \\
  --unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080 \\
  --ozone-platform=wayland \\
  --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection \\
  --touch-events=enabled \\
  --disable-pinch \\
  --overscroll-history-navigation=0 \\
  --disable-translate \\
  --disable-features=Translate,OptimizationHints \\
  --user-data-dir=/tmp/chromium_magi_profile \\
  --window-size=1024,600 \\
  --window-position=0,0 \\
  http://127.0.0.1:8080/ &
"""

environment_content = """XCURSOR_THEME=Adwaita
XCURSOR_SIZE=24
WLR_BACKENDS=drm
WLR_RENDERER=gles2
LIBSEAT_BACKEND=seatd
SEATD_VTBOUND=0
XDG_SESSION_TYPE=wayland
WAYLAND_DISPLAY=wayland-0
"""

sftp = client.open_sftp()
with sftp.open('/home/alonso/.config/labwc/rc.xml', 'w') as f:
    f.write(rc_xml_content)
with sftp.open('/home/alonso/.config/labwc/autostart', 'w') as f:
    f.write(autostart_content)
with sftp.open('/home/alonso/.config/labwc/environment', 'w') as f:
    f.write(environment_content)
sftp.close()

user_run("chmod +x /home/alonso/.config/labwc/autostart")
print("[OK] Archivos de configuración de labwc actualizados en ~/.config/labwc/")

# 2. Configurar magi-kiosk.service con labwc
print("\n--- PASO 2: Configuración de magi-kiosk.service con Labwc ---")
labwc_service = """[Unit]
Description=MAGI Wayland Kiosk Compositor (Core 1 - Interactive Labwc)
After=network.target systemd-user-sessions.service magi-ui.service seatd.service
Wants=magi-ui.service seatd.service

[Service]
User=alonso
Group=alonso
SupplementaryGroups=video input render tty dialout bluetooth
StandardInput=null
StandardOutput=journal
StandardError=journal
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WAYLAND_DISPLAY=wayland-0
Environment=WLR_BACKENDS=drm
Environment=WLR_RENDERER=gles2
Environment=LIBSEAT_BACKEND=seatd
Environment=SEATD_VTBOUND=0
Environment=XDG_SESSION_TYPE=wayland
Environment=XCURSOR_SIZE=24
Environment=XCURSOR_THEME=Adwaita
ExecStart=/usr/bin/labwc -s "/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --no-default-browser-check --disable-session-crashed-bubble --remote-debugging-port=9222 --use-fake-ui-for-media-stream --unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080 --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection --touch-events=enabled --disable-pinch --overscroll-history-navigation=0 --disable-translate --disable-features=Translate,OptimizationHints --user-data-dir=/tmp/chromium_magi_profile --window-size=1024,600 --window-position=0,0 http://127.0.0.1:8080/"
Restart=always
RestartSec=2s
CPUAffinity=1

[Install]
WantedBy=graphical.target
"""

sftp = client.open_sftp()
with sftp.open('/tmp/magi-kiosk.service', 'w') as f:
    f.write(labwc_service)
sftp.close()

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service")

# 3. Guardar en repositorio local
local_svc_path = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
with open(local_svc_path, 'w', encoding='utf-8') as f:
    f.write(labwc_service)

digital_twin_svc = os.path.join(local_root, 'Digital_Twin_Workspace', 'etc', 'systemd', 'system', 'magi-kiosk.service')
with open(digital_twin_svc, 'w', encoding='utf-8') as f:
    f.write(labwc_service)

# 4. Habilitar y reiniciar servicios formalmente
print("\n--- PASO 3: Habilitación e Inicialización del Servicio Labwc ---")
sudo_run("rm -rf /tmp/chromium_magi_profile /run/user/1000/wayland-* || true")
sudo_run("systemctl daemon-reload")
sudo_run("systemctl enable --now magi-kiosk.service")
sudo_run("systemctl restart seatd magi-ui magi-kiosk")

print("[+] Esperando 10 segundos a que Labwc y Chromium se estabilicen...")
time.sleep(10)

# 5. Auditoría del silicio en vivo
print("\n--- PASO 4: Auditoría Forense de Procesos y Descriptores ---")
sudo_run("systemctl status seatd --no-pager")
sudo_run("systemctl status magi-kiosk --no-pager")
user_run("ps -eo pid,psr,stat,comm,args | grep -E 'labwc|chromium|python3' | grep -v grep")
sudo_run("fuser -v /dev/input/event* /dev/dri/card* || true")

# 6. Captura pericial del framebuffer físico
print("\n--- PASO 5: Captura Pericial del Framebuffer Físico ---")
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/magi_screen_labwc_live.png")

telemetry_dir = os.path.join(local_root, 'telemetry')
os.makedirs(telemetry_dir, exist_ok=True)
sftp = client.open_sftp()
sftp.get('/tmp/magi_screen_labwc_live.png', os.path.join(telemetry_dir, 'magi_screen_labwc_live.png'))
sftp.close()
print("[OK] Captura de Labwc descargada a telemetry/magi_screen_labwc_live.png")

client.close()
print("\n[✓] MIGRACIÓN A LABWC Y HABILITACIÓN DE SERVICIO COMPLETADA CON ÉXITO.")
