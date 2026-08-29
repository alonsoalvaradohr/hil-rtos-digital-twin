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

local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Crear configuración rc.xml con mapeo explícito de libinput y touch
rc_xml = """<?xml version="1.0" encoding="UTF-8"?>
<labwc_config>
  <core>
    <decoration>none</decoration>
    <gap>0</gap>
  </core>
  <focus>
    <followMouse>yes</followMouse>
    <raiseOnFocus>yes</raiseOnFocus>
  </focus>
  <keyboard>
    <defaultToPoll>no</defaultToPoll>
  </keyboard>
  <touch>
    <mapToOutput>HDMI-A-1</mapToOutput>
  </touch>
  <libinput>
    <device category="touch">
      <calibrationMatrix>1 0 0 0 1 0</calibrationMatrix>
    </device>
  </libinput>
  <windowRules>
    <windowRule identifier="*" serverDecoration="no">
      <action name="Maximize"/>
      <action name="Focus"/>
      <action name="Raise"/>
    </windowRule>
  </windowRules>
</labwc_config>
"""

sftp = client.open_sftp()
with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(rc_xml)

# Guardar copia local en workspace
labwc_local_dir = os.path.join(local_root, 'Digital_Twin_Workspace', 'home', 'alonso', '.config', 'labwc')
os.makedirs(labwc_local_dir, exist_ok=True)
with open(os.path.join(labwc_local_dir, 'rc.xml'), 'w', encoding='utf-8') as f:
    f.write(rc_xml)

# 2. Actualizar script ~/start_kiosk_local.sh
start_script = """#!/bin/bash
# Script de Lanzamiento Local Directo en Consola Fisica tty1
echo "=== INICIANDO ENTORNO GRAFICO LOCAL LABWC / CHROMIUM (TOUCH MAP CANONICO) ==="
rm -rf /tmp/chromium_magi_profile/Singleton* /run/user/1000/wayland-* 2>/dev/null || true

export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export WLR_BACKENDS=drm
export WLR_RENDERER=gles2
export XCURSOR_THEME=Adwaita
export XCURSOR_SIZE=24

exec labwc -s "/usr/bin/chromium-browser --no-sandbox --kiosk --ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection --touch-events=enabled http://127.0.0.1:8080"
"""

with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(start_script)
sftp.close()

user_run("chmod +x [HOME_REDACTED]")
print("[OK] rc.xml y ~/start_kiosk_local.sh actualizados con éxito en la Raspberry Pi 5.")

client.close()
