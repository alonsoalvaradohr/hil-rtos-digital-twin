import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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

# Limpiar sockets
run('rm -f /run/user/1000/wayland-*')

# Probar cage en modo DRM nativo con log de depuracion detallado
test_cmd = 'env XDG_RUNTIME_DIR=/run/user/1000 WLR_BACKENDS=drm WLR_DRM_DEVICES=/dev/dri/card1 WLR_RENDERER=gles2 WLR_NO_HARDWARE_CURSORS=1 LIBSEAT_BACKEND=builtin cage -d -- true 2>&1'
run(test_cmd)

# Probar tambien con LIBSEAT_BACKEND=seatd
test_cmd2 = 'env XDG_RUNTIME_DIR=/run/user/1000 WLR_BACKENDS=drm WLR_DRM_DEVICES=/dev/dri/card1 WLR_RENDERER=gles2 WLR_NO_HARDWARE_CURSORS=1 LIBSEAT_BACKEND=seatd cage -d -- true 2>&1'
run(test_cmd2)

client.close()

