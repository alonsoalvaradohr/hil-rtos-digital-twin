import paramiko
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env

env = load_env()
sudo_pass = env.get("HIL_SUDO_PASS", "2077")
host = env.get("HIL_SSH_HOST", "AlonsoRTOS")
user = env.get("HIL_SSH_USER", "alonso")
key_path = os.path.expanduser(env.get("HIL_SSH_KEY_PATH", "~/.ssh/id_ed25519_hil"))

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print(f"[+] Conectando a {host} para Fase 0 - Auditoria Kernel en Tiempo Real...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, key_filename=key_path)

def run(cmd):
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print(f"[STDERR]: {err}")
    return out

run("dmesg -T | grep -iE 'underrun|v3d|vc4|drm|crtc|plane|hpd|timeout|flip' | tail -n 45")
run("journalctl -k -n 80 --no-pager")
run("cat /sys/class/drm/card1-HDMI-A-1/modes")
run("cat /sys/class/drm/card1-HDMI-A-1/enabled")
run("cat /sys/class/drm/card1-HDMI-A-1/dpms")
run("cat /boot/firmware/config.txt")
run("cat /proc/interrupts | grep -iE 'vc4|v3d|hdmi|drm'")

client.close()
