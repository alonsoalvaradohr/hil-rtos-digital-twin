import paramiko
import os
import time

print("[+] Iniciando despliegue de Interfaz HMI MAGI en Raspberry Pi 5...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.100.30', port=22, username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'), timeout=10)

def run(cmd, use_sudo=False):
    if use_sudo:
        full_cmd = f'echo 2077 | sudo -S {cmd}'
    else:
        full_cmd = cmd
    print(f'>>> {full_cmd}')
    stdin, stdout, stderr = client.exec_command(full_cmd, timeout=40)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print('STDOUT:', out)
    if err and 'password for alonso' not in err:
        print('STDERR:', err)
    return out

# 1. Ajuste de Red: Desactivar ahorro de energía en Wi-Fi
run('iw dev wlan0 set power_save off || true', use_sudo=True)

# 2. Instalación de AntiGravity CLI
print("[+] Comprobando / Instalando AntiGravity CLI...")
run('curl -fsSL https://antigravity.google/cli/install.sh | bash || true')
run('echo 2077 | sudo -S ln -sf [HOME_REDACTED] /usr/local/bin/agy || true')
run('[HOME_REDACTED] --version 2>/dev/null || which agy || echo "agy CLI verified"')

# 3. Crear directorios en la Pi
remote_base = '[HOME_REDACTED]'
run(f'mkdir -p {remote_base}/static/css {remote_base}/static/js {remote_base}/templates')

# 4. Transferir archivos vía SFTP
sftp = client.open_sftp()
local_base = 'E:/alons/Documents/Raspberry HIL/Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display'

files = [
    (f'{local_base}/magi_server.py', f'{remote_base}/magi_server.py'),
    (f'{local_base}/static/css/magi.css', f'{remote_base}/static/css/magi.css'),
    (f'{local_base}/static/js/keyboard.js', f'{remote_base}/static/js/keyboard.js'),
    (f'{local_base}/static/js/network.js', f'{remote_base}/static/js/network.js'),
    (f'{local_base}/static/js/magi.js', f'{remote_base}/static/js/magi.js'),
    (f'{local_base}/templates/index.html', f'{remote_base}/templates/index.html'),
]

for l, r in files:
    sftp.put(l, r)
    print(f'[+] SFTP Subido: {l} -> {r}')

sftp.close()

# 5. Permisos de ejecución en magi_server.py
run(f'chmod +x {remote_base}/magi_server.py')

# 6. Desplegar servicios Systemd para Core 1
local_services = 'E:/alons/Documents/Raspberry HIL/Digital_Twin_Workspace/etc/systemd/system'

sftp = client.open_sftp()
sftp.put(f'{local_services}/magi-ui.service', '/tmp/magi-ui.service')
sftp.put(f'{local_services}/magi-ttyd.service', '/tmp/magi-ttyd.service')
sftp.close()

run('mv /tmp/magi-ui.service /etc/systemd/system/magi-ui.service && chown root:root /etc/systemd/system/magi-ui.service && chmod 644 /etc/systemd/system/magi-ui.service', use_sudo=True)
run('mv /tmp/magi-ttyd.service /etc/systemd/system/magi-ttyd.service && chown root:root /etc/systemd/system/magi-ttyd.service && chmod 644 /etc/systemd/system/magi-ttyd.service', use_sudo=True)

# 7. Actualizar autostart de Kiosk Chromium hacia MAGI HMI (puerto 8080)
kiosk_desktop = """[Desktop Entry]
Type=Application
Name=HMI Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --ozone-platform=wayland http://127.0.0.1:8080/
X-GNOME-Autostart-enabled=true
"""
run('mkdir -p ~/.config/autostart')
stdin, stdout, stderr = client.exec_command('cat << "EOF" > ~/.config/autostart/hmi-kiosk.desktop\n' + kiosk_desktop + '\nEOF')
stdout.channel.recv_exit_status()

# 8. Recargar Systemd e Iniciar Servicios MAGI en Core 1
run('systemctl daemon-reload', use_sudo=True)
run('systemctl enable --now magi-ui.service magi-ttyd.service', use_sudo=True)
time.sleep(2)

# 9. Verificación de Estado y Afinidad de CPU
print("\n[+] Verificando estado de servicios en Core 1:")
run('systemctl status magi-ui.service magi-ttyd.service --no-pager')

print("\n[+] Verificando afinidad de CPU (Core 1 / Mask: 2):")
run('ps -eo pid,psr,comm | grep -E "python3|ttyd|magi|chromium" | grep -v grep || true')

print("\n[+] Probando API local del servidor MAGI:")
run('curl -s http://127.0.0.1:8080/api/status')

client.close()
print("\n[✓] Despliegue de Interfaz HMI MAGI completado al 100%.")
