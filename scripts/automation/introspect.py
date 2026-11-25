# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
import paramiko
import json
import os
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.100.30', port=22, username='alonso', key_filename=os.path.expanduser('~/.ssh/id_ed25519_hil'))

commands = {
    'board_model': 'cat /proc/device-tree/model 2>/dev/null',
    'serial_number': 'cat /proc/device-tree/serial-number 2>/dev/null',
    'revision': 'xxd -p /proc/device-tree/system/linux,revision 2>/dev/null || cat /proc/cpuinfo | grep Revision',
    'uname': 'uname -a',
    'version': 'cat /proc/version',
    'cmdline': 'cat /proc/cmdline',
    'os_release': 'cat /etc/os-release',
    'debian_version': 'cat /etc/debian_version',
    'lscpu': 'lscpu',
    'cpuinfo': 'cat /proc/cpuinfo',
    'temperature': 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null',
    'free': 'free -h',
    'free_bytes': 'free -b',
    'meminfo': 'cat /proc/meminfo',
    'swapon': 'swapon --show',
    'lsblk': 'lsblk -f -a',
    'df': 'df -hT',
    'fstab': 'cat /etc/fstab',
    'mounts': 'mount | grep -E "^/dev"',
    'cpu_isolated': 'cat /sys/devices/system/cpu/isolated 2>/dev/null',
    'cpu_online': 'cat /sys/devices/system/cpu/online 2>/dev/null',
    'cpu_possible': 'cat /sys/devices/system/cpu/possible 2>/dev/null',
    'cpu_present': 'cat /sys/devices/system/cpu/present 2>/dev/null',
    'cpu_governors': 'head -v -n 1 /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null',
    'cpu_cur_freq': 'head -v -n 1 /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null',
    'cpu_avail_governors': 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors 2>/dev/null',
    'cpu_min_freq': 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq 2>/dev/null',
    'cpu_max_freq': 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq 2>/dev/null',
    'ip_link': 'ip -d link',
    'ip_a': 'ip a',
    'ip_r': 'ip r',
    'ip_neigh': 'ip neigh',
    'resolv_conf': 'cat /etc/resolv.conf',
    'nmcli_dev': 'nmcli dev status',
    'nmcli_con': 'nmcli con show',
    'lspci': 'lspci -v 2>/dev/null || lspci 2>/dev/null || echo "None"',
    'lsusb': 'lsusb -v 2>/dev/null || lsusb 2>/dev/null || echo "None"',
    'dev_nodes': 'ls -la /dev/i2c* /dev/spidev* /dev/ttyAMA* /dev/serial* /dev/gpiomem* /dev/gpiochip* /dev/rpi* 2>/dev/null',
    'lsmod': 'lsmod',
    'services_running': 'systemctl list-units --type=service --state=running --no-pager --no-legend',
    'services_enabled': 'systemctl list-unit-files --type=service --state=enabled --no-pager --no-legend',
    'services_failed': 'systemctl list-units --type=service --state=failed --no-pager --no-legend',
    'bash_history': 'cat [HOME_REDACTED] 2>/dev/null',
    'home_tree': 'ls -la [HOME_REDACTED]',
    'boot_firmware_files': 'ls -la /boot/firmware/',
    'boot_config_txt': 'cat /boot/firmware/config.txt 2>/dev/null || cat /boot/config.txt 2>/dev/null',
    'boot_cmdline_txt': 'cat /boot/firmware/cmdline.txt 2>/dev/null || cat /boot/cmdline.txt 2>/dev/null',
    'security_limits': 'cat /etc/security/limits.conf /etc/security/limits.d/* 2>/dev/null',
    'sysctl_rt': 'sysctl -a 2>/dev/null | grep -E "sched|rt|latency|timer|watchdog|overcommit"',
    'dpkg_total_count': 'dpkg -l | grep "^ii" | wc -l',
    'dpkg_packages': 'dpkg-query -W -f=\'${Package} ${Version} ${Status}\n\'',
    'python_version': 'python3 --version 2>/dev/null',
    'pip_packages': 'python3 -m pip list 2>/dev/null',
    'gcc_version': 'gcc --version 2>/dev/null | head -n 1',
    'realtime_limits': 'ulimit -a',
    'rt_threads': 'ps -eo pid,class,rtprio,pri,ni,comm | grep -E "FF|RR|rt" | head -n 40',
}

raw_data = {}
for name, cmd in commands.items():
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    raw_data[name] = out

with open('E:/alons/Documents/Raspberry HIL/Digital_Twin_Workspace/raw_introspection.json', 'w', encoding='utf-8') as f:
    json.dump(raw_data, f, indent=2, ensure_ascii=False)

print(f"Introspection completed. Extracted {len(raw_data)} telemetry nodes.")
client.close()
