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

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f"\n>>> SUDO: {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    return out

def user_run(cmd):
    print(f"\n>>> USER: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    return out

# Inyectar evento táctil del kernel en la posición del botón NETWORK (x=930, y=50)
sudo_run("""
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_SLOT --value 0 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_TRACKING_ID --value 100 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_POSITION_X --value 930 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_POSITION_Y --value 50 --sync
evemu-event /dev/input/event0 --type EV_KEY --code BTN_TOUCH --value 1 --sync
evemu-event /dev/input/event0 --type EV_SYN --code SYN_REPORT --value 0 --sync
sleep 0.15
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_TRACKING_ID --value -1 --sync
evemu-event /dev/input/event0 --type EV_KEY --code BTN_TOUCH --value 0 --sync
evemu-event /dev/input/event0 --type EV_SYN --code SYN_REPORT --value 0 --sync
""")

time.sleep(1)

# Tomar captura con grim
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 /home/alonso/.local/bin/grim /tmp/screen_labwc_hw_touch.png")

local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sftp = client.open_sftp()
sftp.get('/tmp/screen_labwc_hw_touch.png', os.path.join(local_root, 'telemetry', 'screen_labwc_hw_touch.png'))
sftp.close()

client.close()

