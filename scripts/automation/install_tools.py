import paramiko
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
user = env.get('HIL_SSH_USER', 'alonso')
key_path = os.path.expanduser(env.get('HIL_SSH_KEY_PATH', '~/.ssh/id_ed25519_hil'))
sudo_pass = env.get('HIL_SUDO_PASS', '2077')

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.100.30', port=22, username=user, key_filename=key_path, timeout=8)

def sudo_run(cmd):
    full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    print(f">>> {cmd}")
    stdin, stdout, stderr = client.exec_command(full, timeout=120)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)

sudo_run("apt-get install -y evtest libinput-tools wtype")
client.close()
