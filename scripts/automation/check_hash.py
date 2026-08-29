import paramiko
import os
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('AlonsoRTOS', username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

py_code = """
import ctypes

libcrypt = ctypes.CDLL("libcrypt.so.1")
libcrypt.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
libcrypt.crypt.restype = ctypes.c_char_p

h = b"$y$jB5$psmOMZZ957KFuxmAKdIGF/$Mx/Btfy80472MATKGJ0SEwO1F4947QOQeYyTgR5oer8"

def test_p(p_str):
    res = libcrypt.crypt(p_str.encode('utf-8'), h)
    return res == h

bases = [
    "alonso", "Alonso", "ALONSO", "alonsoalvarado", "AlonsoAlvarado", "alonsoalvaradohr",
    "raspberry", "Raspberry", "raspberrypi", "RaspberryPi", "pi", "Pi", "rpi", "RPI", "rpi5", "RPI5",
    "costarica", "CostaRica", "costa_rica", "Costa_Rica", "cr", "CR",
    "hil", "HIL", "hil-rtos", "hil_rtos", "rtos", "RTOS", "preempt", "preempt_rt",
    "nerv", "NERV", "magi", "MAGI", "balthasar", "casper", "melchior",
    "eva01", "EVA01", "eva", "EVA", "supercomputer",
    "admin", "root", "toor", "password", "Password", "1234", "123456", "12345678", "123456789"
]

suffixes = ["", "1", "12", "123", "1234", "123!", "!", "2024", "2025", "2026", "2024!", "2025!", "2026!", "@123", "#123", "RTOS", "_rtos", "12345"]

found = None
for b in bases:
    for s in suffixes:
        for p in [b + s, b.lower() + s, b.capitalize() + s, b.upper() + s]:
            try:
                if test_p(p):
                    found = p
                    print(f"FOUND PASSWORD: {p}")
                    break
            except:
                pass
        if found:
            break
    if found:
        break

if not found:
    print("Not found in quick list")
"""

sftp = client.open_sftp()
with sftp.open('/tmp/check_h.py', 'w') as f:
    f.write(py_code)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_h.py')
print(stdout.read().decode('utf-8', errors='replace').strip())
print(stderr.read().decode('utf-8', errors='replace').strip())

client.close()

