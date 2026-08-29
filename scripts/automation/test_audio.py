import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("[+] Conectando para verificar subsistema de audio ALSA...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

# Crear archivo WAV de prueba
gen_wav = """import wave, math, struct
with wave.open('/tmp/test_tone.wav', 'w') as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(44100)
    for i in range(44100 * 2):
        val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / 44100.0))
        f.writeframes(struct.pack('<hh', val, val))
print('Test WAV tone created.')
"""

stdin, stdout, stderr = client.exec_command(f'python3 -c "{gen_wav}"')
print(stdout.read().decode('utf-8', errors='replace').strip())

# Mapear tarjetas de audio
stdin, stdout, stderr = client.exec_command('aplay -l; arecord -l')
print("\n[+] Dispositivos de audio registrados:")
print(stdout.read().decode('utf-8', errors='replace').strip())

# Probar reproducción en cards detectadas
for dev in ['hw:0,0', 'hw:1,0']:
    cmd = f'aplay -D {dev} /tmp/test_tone.wav 2>&1 || true'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"\n[+] Prueba de reproducción en {dev}:")
    print(out)

client.close()

