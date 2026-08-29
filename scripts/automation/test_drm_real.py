import paramiko
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] Verificando arranque de Cage bajo backend DRM nativo...")
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

# 1. Limpiar procesos
run('pkill -9 -f cage || true')
run('pkill -9 -f chromium || true')
run('pkill -9 -f labwc || true')
run('rm -rf /run/user/1000/wayland-* /tmp/cage_drm.log /tmp/real_screen.png')
time.sleep(2)

# 2. Iniciar Cage con backend DRM puro y banderas canónicas de Chromium
kiosk_cmd = (
    'nohup taskset -c 1 env XDG_RUNTIME_DIR=/run/user/1000 '
    'WLR_BACKENDS=drm WLR_RENDERER=gles2 WLR_NO_HARDWARE_CURSORS=1 LIBSEAT_BACKEND=seatd '
    'cage -s -- /usr/bin/chromium --ozone-platform=wayland --no-sandbox --kiosk '
    '--disable-features=Translate,OptimizationHints --window-size=1024,600 --window-position=0,0 '
    'http://127.0.0.1:8080/ > /tmp/cage_drm.log 2>&1 &'
)
run(kiosk_cmd)
time.sleep(6)

# 3. Inspeccionar procesos
run('ps -eo pid,psr,stat,comm | grep -E "cage|chromium|python3" | grep -v grep')
run('cat /tmp/cage_drm.log | head -n 40')
run('ls -la /run/user/1000/wayland-*')

# 4. Probar captura de pantalla con grim
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] /tmp/real_screen.png 2>/dev/null && ls -lh /tmp/real_screen.png || true')

client.close()

