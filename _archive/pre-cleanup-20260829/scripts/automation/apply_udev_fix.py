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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("AlonsoRTOS", port=22, username=user, key_filename=key_path, timeout=5)

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f"\n=======================================================")
    print(f">>> SUDO: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(full, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

# 1. Crear regla udev para vincular touch, keyboard y mouse a seat0 con uaccess
udev_rule = """# MAGI SYSTEM - HIL Touchscreen & Input Devices for Seat0
ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ENV{ID_SEAT}="seat0", TAG+="seat", TAG+="uaccess", MODE="0660", GROUP="input"
ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="mouse*", ENV{ID_SEAT}="seat0", TAG+="seat", TAG+="uaccess", MODE="0660", GROUP="input"
ACTION=="add|change", SUBSYSTEM=="input", ENV{ID_SEAT}="seat0", TAG+="seat", TAG+="uaccess", MODE="0660", GROUP="input"
"""

sftp = client.open_sftp()
with sftp.open('/tmp/99-magi-touch-input.rules', 'w') as f:
    f.write(udev_rule)
sftp.close()

sudo_run("mv /tmp/99-magi-touch-input.rules /etc/udev/rules.d/99-magi-touch-input.rules")
sudo_run("chown root:root /etc/udev/rules.d/99-magi-touch-input.rules && chmod 644 /etc/udev/rules.d/99-magi-touch-input.rules")
sudo_run("udevadm control --reload && udevadm trigger")

# 2. Verificar que udev ahora etiqueta event0, event1 y event2 con seat0 y uaccess
sudo_run("udevadm info /dev/input/event0 | grep -iE 'seat|tag|uaccess'")
sudo_run("udevadm info /dev/input/event1 | grep -iE 'seat|tag|uaccess'")
sudo_run("udevadm info /dev/input/event2 | grep -iE 'seat|tag|uaccess'")

# 3. Reiniciar daemons gráficos
sudo_run("systemctl restart seatd magi-ui magi-kiosk")
time.sleep(6)

# 4. Verificar qué procesos abrieron los nodos de entrada ahora
sudo_run("fuser -v /dev/input/event* /dev/dri/card* || true")

client.close()
