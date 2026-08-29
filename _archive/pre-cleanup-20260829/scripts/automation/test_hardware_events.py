import paramiko
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))
sudo_pass = env.get("HIL_SUDO_PASS", "2077")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("AlonsoRTOS", port=22, username=user, key_filename=key_path, timeout=5)

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f">>> SUDO: {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=15)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)

def user_run(cmd):
    print(f">>> USER: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]:", err)

# 1. Asegurar que magi-kiosk este activo
sudo_run("systemctl restart magi-kiosk")
user_run("sleep 6")

# 2. Test inyeccion de hardware event en /dev/input/event0 (QDtech MPI7003 touch)
sudo_run("""
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_SLOT --value 0 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_TRACKING_ID --value 42 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_POSITION_X --value 940 --sync
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_POSITION_Y --value 30 --sync
evemu-event /dev/input/event0 --type EV_KEY --code BTN_TOUCH --value 1 --sync
evemu-event /dev/input/event0 --type EV_SYN --code SYN_REPORT --value 0 --sync
sleep 0.1
evemu-event /dev/input/event0 --type EV_ABS --code ABS_MT_TRACKING_ID --value -1 --sync
evemu-event /dev/input/event0 --type EV_KEY --code BTN_TOUCH --value 0 --sync
evemu-event /dev/input/event0 --type EV_SYN --code SYN_REPORT --value 0 --sync
""")

# 3. Test inyeccion de teclado en /dev/input/event1 (HOLTEK keyboard)
# KEY_A = 30
sudo_run("""
evemu-event /dev/input/event1 --type EV_KEY --code KEY_A --value 1 --sync
evemu-event /dev/input/event1 --type EV_KEY --code KEY_A --value 0 --sync
""")

# 4. Capturar pantalla despues del toque fisico sobre /dev/input/event0
user_run("WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 [HOME_REDACTED] /tmp/screen_after_hw_event.png")

client.close()

