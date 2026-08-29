import paramiko
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] Configurando y probando labwc en modo DRM nativo (WLR_BACKENDS=drm)...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

def run(cmd):
    print("\n>>> " + cmd)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print("[STDERR]:", err)
    return out

# 1. Limpiar procesos anteriores
run('pkill -9 -f cage || true')
run('pkill -9 -f labwc || true')
run('pkill -9 -f chromium || true')
run('rm -rf /run/user/1000/wayland-* /tmp/labwc_drm.log /tmp/real_screen.png')
time.sleep(2)

# 2. Configurar rc.xml y environment de labwc
rc_xml = '''<?xml version="1.0"?>
<labwc_config>
  <core>
    <decoration>none</decoration>
    <gap>0</gap>
  </core>
  <windowRules>
    <windowRule identifier="chromium" serverDecoration="no" maximize="yes" />
  </windowRules>
</labwc_config>
'''

env_txt = '''WLR_BACKENDS=drm
WLR_DRM_DEVICES=/dev/dri/card1
WLR_RENDERER=gles2
WLR_NO_HARDWARE_CURSORS=1
LIBSEAT_BACKEND=builtin
XDG_CURRENT_DESKTOP=labwc
XDG_SESSION_TYPE=wayland
OZONE_PLATFORM=wayland
'''

autostart_sh = '''#!/bin/sh
sleep 1
/usr/bin/chromium --kiosk --noerrdialogs --disable-infobars --no-first-run \
  --ozone-platform=wayland --enable-features=OverlayScrollbar --touch-events=enabled \
  --disable-translate --disable-features=Translate,OptimizationHints,TranslateUI \
  --lang=es --window-size=1024,600 --window-position=0,0 http://127.0.0.1:8080/ &
'''

sftp = client.open_sftp()
with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(rc_xml)
with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(env_txt)
with sftp.open('[HOME_REDACTED]', 'w') as f:
    f.write(autostart_sh)
sftp.close()

run('chmod +x ~/.config/labwc/autostart')

# 3. Iniciar labwc en Core 1
run('nohup taskset -c 1 env XDG_RUNTIME_DIR=/run/user/1000 WLR_BACKENDS=drm WLR_DRM_DEVICES=/dev/dri/card1 WLR_RENDERER=gles2 WLR_NO_HARDWARE_CURSORS=1 LIBSEAT_BACKEND=builtin labwc -d > /tmp/labwc_drm.log 2>&1 &')
time.sleep(5)

# 4. Inspeccionar procesos y logs
run('cat /tmp/labwc_drm.log | head -n 45')
run('ps -eo pid,psr,stat,comm | grep -E "labwc|chromium|python3" | grep -v grep')
run('ls -la /run/user/1000/wayland-*')

# 5. Consultar salidas con wlr-randr en wayland-0
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] || true')

client.close()

