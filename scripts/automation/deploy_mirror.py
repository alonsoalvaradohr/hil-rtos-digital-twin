# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def deploy():
    print("[+] Conectando a la Raspberry Pi...")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

    sftp = c.open_sftp()
    remote_base = '[HOME_REDACTED]'
    
    files = [
        ('E:/alons/Documents/Raspberry HIL/src/hmi_ui/magi_server.py', f'{remote_base}/magi_server.py'),
        ('E:/alons/Documents/Raspberry HIL/src/hmi_ui/templates/index.html', f'{remote_base}/templates/index.html'),
        ('E:/alons/Documents/Raspberry HIL/src/hmi_ui/templates/mirror.html', f'{remote_base}/templates/mirror.html'),
    ]
    for local, remote in files:
        print(f"[*] Subiendo {local} -> {remote}")
        sftp.put(local, remote)
    sftp.close()

    sudo_pwd = os.environ.get('HIL_SUDO_PASS', '')
    cmd = f'echo {sudo_pwd} | sudo -S systemctl restart magi-ui.service && sleep 1 && systemctl status magi-ui.service --no-pager' if sudo_pwd else 'sudo systemctl restart magi-ui.service && sleep 1 && systemctl status magi-ui.service --no-pager'
    stdin, stdout, stderr = c.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())

    print("[*] Verificando endpoints locales en puerto 8088 y 8080...")
    cmds = [
        "curl -s -I http://127.0.0.1:8088/mirror",
        "curl -s -I http://127.0.0.1:8080/mirror",
        "curl -s -I http://127.0.0.1:8088/vnc/vnc_lite.html",
        "curl -s -I http://127.0.0.1:8088/terminal/"
    ]
    for cmd in cmds:
        stdin, stdout, stderr = c.exec_command(cmd)
        print(">>>", cmd)
        print(stdout.read().decode().strip())

    c.close()

if __name__ == '__main__':
    deploy()
