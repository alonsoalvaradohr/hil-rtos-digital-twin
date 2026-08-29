import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

def run(cmd):
    print("\n=======================================================")
    print(">>>", cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print("[STDERR]:", err)

run('systemctl status seatd.service --no-pager')
run('ls -la /run/user/1000/')
run('journalctl -u magi-kiosk.service -n 50 --no-pager')
run('which grim slurp wl-copy wlr-randr cage labwc')
run('cat /boot/firmware/config.txt | grep -iE "dtoverlay|vc4|hdmi|display"')

client.close()

