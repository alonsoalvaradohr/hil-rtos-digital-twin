import paramiko
import os
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.100.30', port=22, username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))
sftp = client.open_sftp()

base_twin = 'E:/alons/Documents/Raspberry HIL/Digital_Twin_Workspace'

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# 1. Download specific remote files safely
files_to_sync = [
    ('/boot/firmware/config.txt', f'{base_twin}/boot_firmware/config.txt'),
    ('/boot/firmware/cmdline.txt', f'{base_twin}/boot_firmware/cmdline.txt'),
    ('/etc/systemd/system/hil-ipc.service', f'{base_twin}/etc/systemd/system/hil-ipc.service'),
    ('/etc/systemd/system/hil-rt.service', f'{base_twin}/etc/systemd/system/hil-rt.service'),
    ('/etc/mosquitto/mosquitto.conf', f'{base_twin}/etc/mosquitto/mosquitto.conf'),
    ('/etc/security/limits.conf', f'{base_twin}/etc/security/limits.conf'),
    ('/etc/fstab', f'{base_twin}/etc/fstab'),
    ('/etc/modules', f'{base_twin}/etc/modules'),
    ('/etc/sysctl.conf', f'{base_twin}/etc/sysctl.conf'),
    ('/etc/os-release', f'{base_twin}/etc/os-release'),
    ('/home/alonso/.bashrc', f'{base_twin}/home_alonso/.bashrc'),
    ('/home/alonso/.profile', f'{base_twin}/home_alonso/.profile'),
    ('/home/alonso/.bash_history', f'{base_twin}/home_alonso/.bash_history'),
    ('/home/alonso/.config/autostart/hmi-kiosk.desktop', f'{base_twin}/home_alonso/.config/autostart/hmi-kiosk.desktop'),
    ('/home/alonso/hil_workstation/02_ipc_core/rt_motor.cpp', f'{base_twin}/home_alonso/hil_workstation/02_ipc_core/rt_motor.cpp'),
    ('/home/alonso/hil_workstation/02_ipc_core/ipc_daemon.cpp', f'{base_twin}/home_alonso/hil_workstation/02_ipc_core/ipc_daemon.cpp'),
    ('/home/alonso/hil_workstation/02_ipc_core/LockFreeQueue.hpp', f'{base_twin}/home_alonso/hil_workstation/02_ipc_core/LockFreeQueue.hpp'),
    ('/home/alonso/hil_workstation/02_ipc_core/SharedState.hpp', f'{base_twin}/home_alonso/hil_workstation/02_ipc_core/SharedState.hpp'),
    ('/home/alonso/hil_workstation/01_system_tuning/boot_config/config_original.bak', f'{base_twin}/home_alonso/hil_workstation/01_system_tuning/boot_config/config_original.bak'),
    ('/home/alonso/hil_workstation/01_system_tuning/boot_config/cmdline_original.bak', f'{base_twin}/home_alonso/hil_workstation/01_system_tuning/boot_config/cmdline_original.bak'),
]

synced_files = []
for rem, loc in files_to_sync:
    try:
        ensure_dir(os.path.dirname(loc))
        sftp.get(rem, loc)
        synced_files.append((rem, loc, os.path.getsize(loc)))
        print(f"[+] Synced: {rem} -> {loc}")
    except Exception as e:
        print(f"[-] Could not sync {rem}: {e}")

# 2. Extract hardware maps and system descriptions into hardware_maps/
ensure_dir(f'{base_twin}/hardware_maps')

hw_commands = {
    'cpu_topology.txt': 'lscpu',
    'cpu_isolation_state.txt': 'echo "=== ISOLATED CPUS ==="; cat /sys/devices/system/cpu/isolated; echo "=== GOVERNORS ==="; head -v -n 1 /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; echo "=== FREQUENCIES (kHz) ==="; head -v -n 1 /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq',
    'memory_map.txt': 'cat /proc/meminfo; echo "=== SWAP ==="; swapon --show',
    'pcie_topology.txt': 'lspci -nnvvv 2>/dev/null || lspci -v',
    'usb_topology.txt': 'lsusb -t; echo "=== USB DEVICES ==="; lsusb',
    'gpio_bus_nodes.txt': 'ls -la /dev/gpio* /dev/i2c* /dev/spidev* /dev/ttyAMA* /dev/serial* /dev/rpi* 2>/dev/null',
    'block_devices.txt': 'lsblk -f -a; echo "=== MOUNT TABLE ==="; df -hT',
    'network_interfaces.txt': 'ip -d link; echo "=== IP ADDRESSES ==="; ip a; echo "=== ROUTING ==="; ip r; echo "=== NM CONNECTIONS ==="; nmcli con show; echo "=== NM DEVICES ==="; nmcli dev status',
    'interrupts_map.txt': 'cat /proc/interrupts',
    'realtime_threads.txt': 'ps -eo pid,tid,class,rtprio,pri,ni,psr,comm --sort=-rtprio | grep -E "FF|RR|rt|migration|irq"',
    'loaded_modules.txt': 'lsmod',
}

for out_file, cmd in hw_commands.items():
    stdin, stdout, stderr = client.exec_command(cmd)
    content = stdout.read().decode('utf-8', errors='replace')
    target_path = os.path.join(f'{base_twin}/hardware_maps', out_file)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Generated HW Map: {out_file}")

sftp.close()
client.close()

print(f"\n[OK] Digital Twin synchronization completed. {len(synced_files)} files copied, {len(hw_commands)} hardware maps generated.")
