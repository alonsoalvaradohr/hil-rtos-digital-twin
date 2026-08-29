import os
import sys
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

def run_cmd(cmd, is_sudo=False):
    if is_sudo:
        full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    else:
        full = cmd
    stdin, stdout, stderr = client.exec_command(full, timeout=25)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    return out

report = []
def add_section(title, cmd, is_sudo=False):
    out = run_cmd(cmd, is_sudo)
    report.append(f"=== {title} ===\n{out}\n\n")

add_section("BASH HISTORY", "cat /home/alonso/.bash_history || true")
add_section("GIT BRANCHES & STATUS IN WORKSTATION", "cd /home/alonso/hil_workstation && git status && git branch -a && git log -n 15 --oneline || true")
add_section("ACTIVE PROCESSES", "ps -eo pid,psr,user,comm,args | grep -E 'labwc|chromium|python3|seatd' | grep -v grep")
add_section("LABWC PROCESS ENVIRONMENT", "LABWC_PID=$(pgrep -x labwc | head -n 1); if [ -n \"$LABWC_PID\" ]; then strings /proc/$LABWC_PID/environ; fi")
add_section("CHROMIUM PROCESS ENVIRONMENT", "CHROM_PID=$(pgrep -x chromium | head -n 1); if [ -n \"$CHROM_PID\" ]; then strings /proc/$CHROM_PID/environ; fi")
add_section("SOCKETS IN RUN USER 1000", "ls -la /run/user/1000/ /run/seatd.sock")
add_section("UDEV RULES IN /etc/udev/rules.d", "cat /etc/udev/rules.d/* || true", is_sudo=True)
add_section("SEATD SYSTEMD CONFIG", "systemctl cat seatd.service", is_sudo=True)
add_section("MAGI-KIOSK SYSTEMD CONFIG", "systemctl cat magi-kiosk.service", is_sudo=True)
add_section("MAGI-UI SYSTEMD CONFIG", "systemctl cat magi-ui.service", is_sudo=True)

client.close()

local_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out_file = os.path.join(local_root, 'telemetry', 'forensic_phase13_report.txt')
with open(out_file, 'w', encoding='utf-8') as f:
    f.write("".join(report))

print(f"[OK] Reporte forense guardado en {out_file}")
print("Primeras 150 lineas del reporte:")
print("\n".join("".join(report).splitlines()[:150]))

