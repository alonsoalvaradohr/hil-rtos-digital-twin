import os
import sys
import time
import json
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
            c.connect(h, port=22, username=user, key_filename=key_path, timeout=5)
            return c
        except Exception:
            pass
    raise RuntimeError("No se pudo conectar a ningun host")

client = get_client()
print("[OK] Conectado a la Raspberry Pi")

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f">>> SUDO: {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=40)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

def user_run(cmd):
    print(f">>> USER: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=40)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)
    return out

# 1. Transferencia
print("\n--- PASO 1: Sincronizando Frontend y Systemd Service ---")
local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
local_hmi = os.path.join(local_root, 'src', 'hmi_ui')
remote_hmi = '[HOME_REDACTED]'

def transfer_file(local_file, remote_file):
    with open(local_file, 'rb') as f:
        content = f.read()
    sftp = client.open_sftp()
    with sftp.open(remote_file, 'wb') as rf:
        rf.write(content)
    sftp.close()

transfer_file(os.path.join(local_hmi, 'magi_server.py'), f'{remote_hmi}/magi_server.py')
transfer_file(os.path.join(local_hmi, 'templates', 'index.html'), f'{remote_hmi}/templates/index.html')
transfer_file(os.path.join(local_hmi, 'static', 'css', 'magi.css'), f'{remote_hmi}/static/css/magi.css')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'magi.js'), f'{remote_hmi}/static/js/magi.js')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'network.js'), f'{remote_hmi}/static/js/network.js')
transfer_file(os.path.join(local_hmi, 'static', 'js', 'keyboard.js'), f'{remote_hmi}/static/js/keyboard.js')

local_svc = os.path.join(local_root, 'config', 'systemd', 'magi-kiosk.service')
transfer_file(local_svc, '/tmp/magi-kiosk.service')

local_ws = os.path.join(local_root, 'scripts', 'automation', 'pure_ws_cdp.py')
transfer_file(local_ws, '/tmp/pure_ws_cdp.py')

sudo_run("mv /tmp/magi-kiosk.service /etc/systemd/system/magi-kiosk.service")
sudo_run("chown root:root /etc/systemd/system/magi-kiosk.service && chmod 644 /etc/systemd/system/magi-kiosk.service")
sudo_run("systemctl daemon-reload")
sudo_run("systemctl restart seatd magi-ui magi-kiosk")
print("[+] Esperando 8 segundos a que Chromium inicie con puerto 9222...")
time.sleep(8)

grim_cmd = "WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED]"

print("\n=======================================================")
print("=== EJECUTANDO SECUENCIA FORENSE DE 6 PASOS ===")
print("=======================================================")

# Captura 1: Estado Inicial MAGI Main View
print("\n[1/6] Capturando: 01_magi_main.png")
user_run(f"{grim_cmd} /tmp/01_magi_main.png")

# Captura 2: Click / Hover sobre botón NETWORK
print("\n[2/6] Interactuando: Toque sobre boton NETWORK")
user_run("python3 /tmp/pure_ws_cdp.py \"const btn = document.getElementById('btn-open-network'); btn.style.background='var(--magi-orange)'; btn.style.color='#000'; 'NETWORK_TRIGGERED'\"")
time.sleep(0.3)
user_run(f"{grim_cmd} /tmp/02_click_network.png")

# Captura 3: Panel NETWORK completamente abierto
print("\n[3/6] Desplegando modal NETWORK y escaneando...")
user_run("python3 /tmp/pure_ws_cdp.py \"window.magiNetwork ? window.magiNetwork.open() : document.getElementById('network-modal').style.display='flex'\"")
time.sleep(1.5)
user_run(f"{grim_cmd} /tmp/03_network_panel.png")

# Captura 4: Regreso a pantalla principal MAGI
print("\n[4/6] Cerrando modal NETWORK y regresando a MAGI...")
user_run("python3 /tmp/pure_ws_cdp.py \"window.magiNetwork ? window.magiNetwork.close() : document.getElementById('network-modal').style.display='none'\"")
time.sleep(0.8)
user_run(f"{grim_cmd} /tmp/04_back_to_magi.png")

# Captura 5: Toque sobre Pod BALTHASAR • 2
print("\n[5/6] Interactuando: Toque sobre Pod BALTHASAR • 2")
user_run("python3 /tmp/pure_ws_cdp.py \"const p = document.getElementById('pod-balthasar'); p.style.boxShadow='0 0 30px #FF9900'; p.style.transform='scale(0.98)'; 'BALTHASAR_CLICKED'\"")
time.sleep(0.3)
user_run(f"{grim_cmd} /tmp/05_click_balthasar.png")

# Captura 6: Panel BALTHASAR completamente desplegado
print("\n[6/6] Desplegando Cockpit BALTHASAR • 2...")
user_run("python3 /tmp/pure_ws_cdp.py \"window.magiUI.switchView('balthasar')\"")
time.sleep(1.2)
user_run(f"{grim_cmd} /tmp/06_balthasar_panel.png")

# 4. Descargar las 6 capturas
print("\n--- PASO 4: Descargando las 6 capturas secuenciales al Host (telemetry/) ---")
telemetry_dir = os.path.join(local_root, 'telemetry')
os.makedirs(telemetry_dir, exist_ok=True)

files = [
    "01_magi_main.png",
    "02_click_network.png",
    "03_network_panel.png",
    "04_back_to_magi.png",
    "05_click_balthasar.png",
    "06_balthasar_panel.png"
]

sftp = client.open_sftp()
for f in files:
    remote_path = f"/tmp/{f}"
    local_path = os.path.join(telemetry_dir, f)
    try:
        sftp.get(remote_path, local_path)
        print(f"[✓] Descargado: {f} ({os.path.getsize(local_path)} bytes)")
    except Exception as e:
        print(f"[-] Error descargando {f}: {e}")

sftp.close()
client.close()
print("\n[✓] SECUENCIA COMPLETA DE 6 CAPTURAS FINALIZADA EXITOSAMENTE.")
