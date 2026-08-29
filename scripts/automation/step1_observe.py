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

def run(cmd):
    print(f"\n=======================================================")
    print(f">>> CMD: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print(f"[STDERR]: {err}")

run("systemctl status magi-kiosk.service seatd magi-ui --no-pager -l")
run("ps aux | grep -E 'cage|chromium|magi|seatd' | grep -v grep")
run("groups alonso")
run("ls -la /dev/input/ /dev/dri/")
run("cat /proc/bus/input/devices")
run("journalctl -u magi-kiosk.service -n 50 --no-pager")
run("dmesg -T | grep -iE 'drm|vc4|hdmi|input|touch|segfault|underrun' | tail -40")

client.close()
