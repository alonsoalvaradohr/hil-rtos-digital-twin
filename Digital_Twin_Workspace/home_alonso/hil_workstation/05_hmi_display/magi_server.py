#!/usr/bin/env python3
"""
MAGI SYSTEM - HMI Backend & Touch Network Manager (Evangelion UI)
Host: Raspberry Pi 5 (Core 1 Dedicated)
Port: 8080
"""

import os
import sys
import json
import subprocess
import time
import struct
import mmap
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")

# Constantes de Memoria Compartida
SHM_PATH = "/dev/shm/hil_shm"
HIL_SHM_MAGIC = 0x48494C5F53484D32

def get_system_status():
    status = {
        "hostname": "AlonsoRTOS",
        "system": "MAGI SYSTEM v2.0",
        "kernel": "Linux 6.18.34+rpt-rpi-v8-rt SMP PREEMPT_RT",
        "core_domain": "Core 1 (UI / Touch / Network)",
        "cpu_temp": 50.0,
        "ram_used_mb": 400,
        "ram_total_mb": 15360,
        "wifi_connected": False,
        "wifi_ssid": "Disconnected",
        "ip_address": "127.0.0.1",
        "rt_alive": False,
        "ipc_alive": False,
        "timestamp": time.time()
    }

    try:
        # Temperatura SoC
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                status["cpu_temp"] = round(float(f.read().strip()) / 1000.0, 1)

        # Estado de Red Wi-Fi
        res = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"], 
                             capture_output=True, text=True, timeout=2)
        for line in res.stdout.strip().split("\n"):
            parts = line.split(":")
            if len(parts) >= 4 and parts[1] == "wifi" and parts[2] == "connected":
                status["wifi_connected"] = True
                status["wifi_ssid"] = parts[3]

        # IP Address
        ip_res = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        ips = ip_res.stdout.strip().split()
        if ips:
            status["ip_address"] = ips[0]

        # Estado de SHM y Heartbeats
        if os.path.exists(SHM_PATH):
            with open(SHM_PATH, "r+b") as f:
                mm = mmap.mmap(f.fileno(), 1024, mmap.MAP_SHARED, mmap.PROT_READ)
                magic, version, is_init = struct.unpack_from("<QII", mm, 0)
                if magic == HIL_SHM_MAGIC:
                    rt_hb = struct.unpack_from("<Q", mm, 64)[0]
                    ipc_hb = struct.unpack_from("<Q", mm, 128)[0]
                    status["rt_alive"] = (rt_hb > 0)
                    status["ipc_alive"] = (ipc_hb > 0)
                mm.close()
    except Exception as e:
        status["error"] = str(e)

    return status

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    return jsonify(get_system_status())

@app.route("/api/wifi/scan")
def api_wifi_scan():
    networks = []
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,CHAN", "dev", "wifi", "list"],
            capture_output=True, text=True, timeout=6
        )
        seen_ssids = set()
        for line in res.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 4 and parts[0]:
                ssid = parts[0]
                if ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    networks.append({
                        "ssid": ssid,
                        "signal": int(parts[1]) if parts[1].isdigit() else 0,
                        "security": parts[2] if parts[2] else "Open",
                        "channel": parts[3],
                        "rate": "54 Mbit/s"
                    })
        networks.sort(key=lambda x: x["signal"], reverse=True)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "networks": []}), 500

    return jsonify({"success": True, "networks": networks})

@app.route("/api/wifi/connect", methods=["POST"])
def api_wifi_connect():
    data = request.get_json(force=True)
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()

    if not ssid:
        return jsonify({"success": False, "message": "SSID no especificado"}), 400

    try:
        cmd = ["sudo", "nmcli", "dev", "wifi", "connect", ssid]
        if password:
            cmd.extend(["password", password])

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode == 0:
            return jsonify({"success": True, "message": f"Conectado exitosamente a {ssid}", "output": res.stdout})
        else:
            return jsonify({"success": False, "message": f"Error de conexión: {res.stderr}", "output": res.stderr}), 400
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "Tiempo de espera agotado al autenticar red"}), 504
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/wifi/disconnect", methods=["POST"])
def api_wifi_disconnect():
    try:
        res = subprocess.run(["sudo", "nmcli", "dev", "disconnect", "wlan0"], 
                             capture_output=True, text=True, timeout=5)
        return jsonify({"success": True, "message": "Interfaz Wi-Fi desconectada"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/bluetooth/scan")
def api_bluetooth_scan():
    devices = []
    try:
        res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=3)
        paired_res = subprocess.run(["bluetoothctl", "paired-devices"], capture_output=True, text=True, timeout=3)
        paired_macs = set()
        for line in paired_res.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "Device":
                paired_macs.add(parts[1])

        for line in res.stdout.strip().split("\n"):
            parts = line.split(maxsplit=2)
            if len(parts) >= 3 and parts[0] == "Device":
                mac = parts[1]
                name = parts[2]
                devices.append({
                    "mac": mac,
                    "name": name,
                    "paired": (mac in paired_macs)
                })
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "devices": []})

    return jsonify({"success": True, "devices": devices})

@app.route("/api/hil/command", methods=["POST"])
def api_hil_command():
    data = request.get_json(force=True)
    action_id = data.get("action_id", 1)
    target_speed = float(data.get("speed", 0.0))
    flags = data.get("flags", 1) # CTRL_FLAG_MOTOR_ENABLE

    # Publicar comando a MQTT
    payload = json.dumps({"action_id": action_id, "speed": target_speed, "flags": flags})
    try:
        subprocess.run(["mosquitto_pub", "-t", "hil/command", "-m", payload], timeout=1)
        return jsonify({"success": True, "command_sent": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("[+] MAGI SYSTEM Server iniciando en Core 1 (0.0.0.0:8080)...")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
