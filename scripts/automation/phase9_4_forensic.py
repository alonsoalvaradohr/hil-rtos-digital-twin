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

print(f"[+] Conectando a {host} para FASE 0 - AUDITORIA FORENSE PROFUNDA DE CRASH-LOOP...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, key_filename=key_path)

def run(cmd):
    print(f"\n=======================================================")
    print(f"=== [EXEC]: {cmd}")
    print(f"=======================================================")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print(f"[STDERR]: {err}")
    return out

run("journalctl -u magi-kiosk.service -n 100 --no-pager")
run("coredumpctl list 2>&1 || echo 'No coredumpctl'")
run("dmesg -T | grep -iE 'segfault|gpu|v3d|vc4|oom|out of memory|fatal|trap' | tail -n 40")
run("ps aux | grep -E 'cage|chromium|magi' | grep -v grep")
run("systemctl status magi-kiosk.service magi-ui.service --no-pager")

client.close()

