import paramiko
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] Iniciando Kiosk con Cage optimizado y capturando screenshot...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

# 1. Subir archivos
sftp = client.open_sftp()
sftp.put('E:/alons/Documents/Raspberry HIL/src/hmi_ui/templates/index.html', '/home/alonso/hil_workstation/05_hmi_display/templates/index.html')
sftp.put('E:/alons/Documents/Raspberry HIL/src/hmi_ui/magi_server.py', '/home/alonso/hil_workstation/05_hmi_display/magi_server.py')
sftp.close()

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

# 2. Limpieza de procesos anteriores
run('pkill -9 -f cage || true')
run('pkill -9 -f labwc || true')
run('pkill -9 -f chromium || true')
run('rm -rf /run/user/1000/wayland-* /tmp/magi_screen.png /tmp/chromium_kiosk')
time.sleep(2)

# 3. Lanzar cage en Core 1 con resolución 1024x600 y supresión total de diálogos y translate
kiosk_cmd = (
    'nohup taskset -c 1 env XDG_RUNTIME_DIR=/run/user/1000 WLR_NO_HARDWARE_CURSORS=1 WLR_RENDERER=gles2 '
    'WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 '
    'cage -s -- /usr/bin/chromium --user-data-dir=/tmp/chromium_kiosk --kiosk --noerrdialogs --disable-infobars --no-first-run '
    '--ozone-platform=wayland --enable-features=OverlayScrollbar --touch-events=enabled '
    '--disable-translate --disable-features=Translate,OptimizationHints,TranslateUI '
    '--lang=es --window-size=1024,600 --window-position=0,0 http://127.0.0.1:8080/ > /tmp/cage_kiosk.log 2>&1 &'
)
run(kiosk_cmd)
time.sleep(6)

# 4. Capturar pantalla con grim
run('WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/magi_screen.png && ls -lh /tmp/magi_screen.png')

# 5. Descargar imagen al host
sftp = client.open_sftp()
sftp.get('/tmp/magi_screen.png', 'E:/alons/Documents/Raspberry HIL/magi_screen.png')
sftp.close()

size = os.path.getsize('E:/alons/Documents/Raspberry HIL/magi_screen.png')
print(f"\n[OK] Screenshot final descargado: E:/alons/Documents/Raspberry HIL/magi_screen.png ({size} bytes)")

client.close()

