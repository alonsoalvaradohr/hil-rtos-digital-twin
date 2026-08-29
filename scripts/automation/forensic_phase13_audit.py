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
print("[OK] Conectado exitosamente a la Raspberry Pi 5")

def run_cmd(title, cmd, is_sudo=False):
    print(f"\n======================================================================")
    print(f"=== {title}")
    print(f"======================================================================")
    if is_sudo:
        full = f"echo '{sudo_pass}' | sudo -S bash -c \"{cmd}\""
    else:
        full = cmd
    stdin, stdout, stderr = client.exec_command(full, timeout=25)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and '[sudo]' not in err: print("[STDERR]:", err)
    return out

# 1. Historial de comandos
run_cmd("HISTORIAL DE BASH (~/.bash_history)", "tail -n 80 /home/alonso/.bash_history || true")

# 2. Estado de repositorios Git en la Pi
run_cmd("GIT STATUS Y LOG EN /home/alonso/hil_workstation", "cd /home/alonso/hil_workstation && git status && git branch -a && git log -n 10 --oneline || echo 'No git repo in hil_workstation'")

# 3. Entorno de procesos Labwc y Chromium
run_cmd("PROCESOS GRAFICOS ACTIVOS", "ps -eo pid,psr,user,comm,args | grep -E 'labwc|chromium|python3|seatd' | grep -v grep")

run_cmd("ENTORNO DE LABWC (PID)", "LABWC_PID=$(pgrep -x labwc | head -n 1); if [ -n \"$LABWC_PID\" ]; then strings /proc/$LABWC_PID/environ | grep -E 'WAYLAND|XDG|LIBSEAT|SEATD|DISPLAY|XCURSOR'; fi")

run_cmd("ENTORNO DE CHROMIUM (PID)", "CHROM_PID=$(pgrep -x chromium | head -n 1); if [ -n \"$CHROM_PID\" ]; then strings /proc/$CHROM_PID/environ | grep -E 'WAYLAND|XDG|LIBSEAT|SEATD|DISPLAY|XCURSOR'; fi")

# 4. Sockets y permisos en /run/user/1000
run_cmd("SOCKETS EN /run/user/1000", "ls -la /run/user/1000/ /run/seatd.sock")

# 5. Configuración activa de labwc
run_cmd("CONFIGURACIÓN LABWC (~/.config/labwc/rc.xml)", "cat /home/alonso/.config/labwc/rc.xml")
run_cmd("CONFIGURACIÓN LABWC (~/.config/labwc/environment)", "cat /home/alonso/.config/labwc/environment")

# 6. Unidades systemd activas
run_cmd("SYSTEMD CAT magi-kiosk.service", "systemctl cat magi-kiosk.service")
run_cmd("SYSTEMD CAT seatd.service", "systemctl cat seatd.service")

# 7. Últimos logs de journal
run_cmd("JOURNALCTL magi-kiosk (ultimas 30 lineas)", "journalctl -u magi-kiosk -n 30 --no-pager")
run_cmd("JOURNALCTL seatd (ultimas 20 lineas)", "journalctl -u seatd -n 20 --no-pager")

client.close()

