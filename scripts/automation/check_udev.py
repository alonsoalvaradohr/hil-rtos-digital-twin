import os
import sys
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
    print(f">>> SUDO: {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=20)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)

sudo_run("udevadm info /dev/input/event0")
sudo_run("udevadm info /dev/input/event1")
sudo_run("udevadm info /dev/input/event2")

client.close()
