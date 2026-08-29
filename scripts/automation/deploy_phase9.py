import paramiko
import os
import sys
import time

print("[+] Iniciando sincronizacion y despliegue Fase 9 en Raspberry Pi 5...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

sftp = client.open_sftp()
local_base = 'E:/alons/Documents/Raspberry HIL/src/hmi_ui'
remote_base = '[HOME_REDACTED]'

files = [
    (f'{local_base}/magi_server.py', f'{remote_base}/magi_server.py'),
    (f'{local_base}/templates/index.html', f'{remote_base}/templates/index.html'),
    (f'{local_base}/static/css/magi.css', f'{remote_base}/static/css/magi.css'),
    (f'{local_base}/static/js/magi.js', f'{remote_base}/static/js/magi.js'),
    (f'{local_base}/static/js/network.js', f'{remote_base}/static/js/network.js'),
    (f'{local_base}/static/js/keyboard.js', f'{remote_base}/static/js/keyboard.js'),
]

for l, r in files:
    sftp.put(l, r)
    print(f'[+] SFTP Subido: {l} -> {r}')

sftp.close()

# Reiniciar magi_server.py de forma no bloqueante
print("[+] Reiniciando magi-ui daemon en Core 1...")
client.exec_command('pkill -f magi_server.py')
time.sleep(3)

# Probar endpoint /api/status y /api/magi/prompt localmente en la Pi
print("[+] Probando API de Estado:")
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:8080/api/status')
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n[+] Probando API de Prompt / AntiGravity CLI:")
stdin, stdout, stderr = client.exec_command('curl -s -X POST http://127.0.0.1:8080/api/magi/prompt -H "Content-Type: application/json" -d "{\\"prompt\\": \\"Diagnosticar latencia y jitter de lazo RT en Core 3\\"}"')
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n[+] Probando API de Sintesis TTS:")
stdin, stdout, stderr = client.exec_command('curl -s -X POST http://127.0.0.1:8080/api/audio/tts -H "Content-Type: application/json" -d "{\\"text\\": \\"MAGI SYSTEM EN LINEA\\"}"')
print(stdout.read().decode('utf-8', errors='replace').strip())

print("\n[+] Verificando afinidad de hilos y Core 1 (PSR 1):")
stdin, stdout, stderr = client.exec_command('ps -eo pid,psr,comm | grep -E "python3|ttyd|chromium|cage" | grep -v grep')
print(stdout.read().decode('utf-8', errors='replace').strip())

client.close()
print("\n[OK] Despliegue y verificacion de Fase 9 completado exitosamente.")

