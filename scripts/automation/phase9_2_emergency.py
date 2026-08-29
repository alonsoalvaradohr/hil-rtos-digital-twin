import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] Conectando para PARADA DE EMERGENCIA Y CONTENCION (Fase 0)...")
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

# Detención inmediata de procesos gráficos colgados
run('pkill -9 -f cage || true')
run('pkill -9 -f chromium || true')
run('pkill -9 -f labwc || true')

# Detención de servicios
run('systemctl stop magi-kiosk.service 2>/dev/null || true')
run('systemctl disable magi-kiosk.service 2>/dev/null || true')

# Inspección de kernel y DRM
run('dmesg | grep -iE "drm|vc4|hdmi|underrun|reset|segfault" | tail -n 30')
run('ls -la /dev/dri/')
run('fuser -v /dev/dri/* 2>&1 || true')
run('cat /boot/firmware/cmdline.txt')
run('cat /sys/class/drm/card1-HDMI-A-1/status 2>/dev/null || echo "No status card1-HDMI-A-1"')
run('cat /sys/class/drm/card1-HDMI-A-2/status 2>/dev/null || echo "No status card1-HDMI-A-2"')

client.close()

