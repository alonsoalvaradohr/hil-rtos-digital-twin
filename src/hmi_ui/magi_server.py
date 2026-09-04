#!/usr/bin/env python3
"""
MAGI SYSTEM - HMI Backend & Touch Network Manager (Evangelion Supercomputer HMI)
Host: Raspberry Pi 5 (Core 1 Dedicated Sandboxed Domain)
Port: 8080
"""

import os
import sys
import json
import subprocess
import time
import struct
import mmap
import re
import ipaddress
import signal
import threading
from urllib.parse import urlsplit
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Constantes de Memoria Compartida
SHM_PATH = "/dev/shm/hil_shm"
HIL_SHM_MAGIC = 0x48494C5F53484D32

AGY_TIMEOUT_SECONDS = float(os.environ.get("MAGI_AGY_TIMEOUT_SECONDS", "45"))
AGY_SUMMARY_TIMEOUT_SECONDS = float(os.environ.get("MAGI_AGY_SUMMARY_TIMEOUT_SECONDS", "20"))
NETWORK_TIMEOUT_SECONDS = float(os.environ.get("MAGI_NETWORK_TIMEOUT_SECONDS", "15"))
BLUETOOTH_TIMEOUT_SECONDS = float(os.environ.get("MAGI_BLUETOOTH_TIMEOUT_SECONDS", "20"))
BLUETOOTH_MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
OSK_EXECUTABLE = "/usr/bin/wvkbd-mobintl"
OSK_ENVIRONMENT = {"XDG_RUNTIME_DIR": "/run/user/1000", "WAYLAND_DISPLAY": "wayland-0"}
OSK_ALLOWED_ORIGINS = {"http://127.0.0.1:8080", "http://localhost:8080"}
_osk_lock = threading.Lock()
_osk_process = None
_osk_pid = None


def _command_result(command, timeout, env=None, input_text=None):
    """Ejecuta un comando acotado y conserva evidencia literal del resultado."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, env=env,
            input=input_text
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "returncode": None, "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "returncode": None, "stdout": "", "stderr": str(exc),
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
            "timed_out": False,
        }


def _failure_summary(result):
    if result["timed_out"]:
        return "La solicitud no finalizo dentro del tiempo permitido. No se asumio ningun resultado."
    detail = result["stderr"] or result["stdout"] or "sin salida de diagnostico"
    return f"La ejecucion fallo (codigo {result['returncode']}): {detail}"


def _agy_environment():
    env = os.environ.copy()
    env["PATH"] = "/home/alonso/.local/bin:/usr/local/bin:" + env.get("PATH", "")
    return env


def _summarize_for_tts(prompt, primary_result):
    """Solicita solo un resumen textual; la segunda llamada no recibe autoridad operativa."""
    evidence = primary_result["stdout"] if primary_result["returncode"] == 0 else _failure_summary(primary_result)
    summary_prompt = (
        "TAREA ESTRICTAMENTE NO OPERATIVA: resume en espanol para lectura TTS la evidencia "
        "incluida abajo. No ejecutes comandos, no uses herramientas, no declares exito si la "
        "evidencia indica fallo. Responde solamente con 1 a 3 frases factuales.\n"
        f"Solicitud original: {prompt}\nEvidencia: {evidence[:12000]}"
    )
    result = _command_result(
        ["taskset", "-c", "1", "agy", "-p", summary_prompt],
        AGY_SUMMARY_TIMEOUT_SECONDS, env=_agy_environment()
    )
    if result["returncode"] == 0 and result["stdout"]:
        return result["stdout"], result
    fallback = ("La operacion termino correctamente. " + primary_result["stdout"][:500]) \
        if primary_result["returncode"] == 0 else _failure_summary(primary_result)
    return fallback, result


def _split_nmcli_line(line):
    """Divide salida terse escapada de nmcli sin romper ':' o '\\' del SSID."""
    fields, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    fields.append("".join(current))
    return fields


def _bluetoothctl(*commands, timeout=BLUETOOTH_TIMEOUT_SECONDS):
    script = "\n".join(commands) + "\nquit\n"
    return _command_result(["bluetoothctl"], timeout, input_text=script)


def _bluetooth_info(mac):
    result = _command_result(["bluetoothctl", "info", mac], BLUETOOTH_TIMEOUT_SECONDS)
    properties = {}
    if result["returncode"] == 0:
        for line in result["stdout"].splitlines():
            if ":" in line:
                key, value = line.strip().split(":", 1)
                properties[key.lower()] = value.strip()
    return result, properties


def _request_is_local(remote_addr, origin):
    """Acepta únicamente clientes loopback y, cuando existe, un Origin kiosk exacto."""
    try:
        if not ipaddress.ip_address(remote_addr or "").is_loopback:
            return False
    except ValueError:
        return False
    if not origin:
        return True
    parsed = urlsplit(origin)
    normalized = f"{parsed.scheme}://{parsed.netloc}"
    return parsed.path in {"", "/"} and not parsed.query and not parsed.fragment and normalized in OSK_ALLOWED_ORIGINS


def _pid_is_osk(pid):
    """Verifica PID, ejecutable exacto y propietario antes de administrarlo."""
    if not isinstance(pid, int) or pid <= 1:
        return False
    try:
        proc_dir = f"/proc/{pid}"
        return os.stat(proc_dir).st_uid == os.geteuid() and os.path.realpath(f"{proc_dir}/exe") == OSK_EXECUTABLE
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return False


def _find_existing_osk():
    try:
        entries = os.scandir("/proc")
    except OSError:
        return None
    with entries:
        for entry in entries:
            if entry.name.isdigit() and _pid_is_osk(int(entry.name)):
                return int(entry.name)
    return None


def _current_osk_pid():
    global _osk_process, _osk_pid
    if _osk_process is not None:
        if _osk_process.poll() is None and _pid_is_osk(_osk_process.pid):
            _osk_pid = _osk_process.pid
            return _osk_pid
        _osk_process = None
        _osk_pid = None
    if _osk_pid is not None and _pid_is_osk(_osk_pid):
        return _osk_pid
    _osk_pid = _find_existing_osk()
    return _osk_pid


def _show_osk():
    global _osk_process, _osk_pid
    existing_pid = _current_osk_pid()
    if existing_pid is not None:
        return {"success": True, "running": True, "pid": existing_pid, "already_running": True}
    if not os.path.isfile(OSK_EXECUTABLE) or not os.access(OSK_EXECUTABLE, os.X_OK):
        return {"success": False, "running": False, "pid": None,
                "error": f"Ejecutable OSK no disponible: {OSK_EXECUTABLE}"}
    env = os.environ.copy()
    env.update(OSK_ENVIRONMENT)
    try:
        process = subprocess.Popen(
            [OSK_EXECUTABLE], env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            start_new_session=True
        )
        time.sleep(0.1)
        returncode = process.poll()
        if returncode is not None:
            stderr = process.stderr.read().strip() if process.stderr else ""
            return {"success": False, "running": False, "pid": process.pid,
                    "returncode": returncode, "error": stderr or "wvkbd finalizo al iniciar"}
        if not _pid_is_osk(process.pid):
            process.terminate()
            return {"success": False, "running": False, "pid": process.pid,
                    "error": "El PID iniciado no corresponde al ejecutable OSK esperado"}
        _osk_process = process
        _osk_pid = process.pid
        return {"success": True, "running": True, "pid": process.pid, "already_running": False}
    except OSError as exc:
        return {"success": False, "running": False, "pid": None, "error": str(exc)}


def _hide_osk(timeout=2.0):
    global _osk_process, _osk_pid
    pid = _current_osk_pid()
    if pid is None:
        return {"success": True, "running": False, "pid": None, "already_stopped": True}
    try:
        if _osk_process is not None and _osk_process.pid == pid:
            _osk_process.terminate()
            try:
                returncode = _osk_process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                _osk_process.kill()
                returncode = _osk_process.wait(timeout=timeout)
        else:
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + timeout
            while _pid_is_osk(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            if _pid_is_osk(pid):
                os.kill(pid, signal.SIGKILL)
                deadline = time.monotonic() + timeout
                while _pid_is_osk(pid) and time.monotonic() < deadline:
                    time.sleep(0.05)
            returncode = None
        still_running = _pid_is_osk(pid)
        _osk_process = None
        _osk_pid = pid if still_running else None
        if still_running:
            return {"success": False, "running": True, "pid": pid, "returncode": returncode,
                    "error": "wvkbd continua activo despues de terminate/kill"}
        return {"success": True, "running": False, "pid": pid, "returncode": returncode}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"success": False, "running": _pid_is_osk(pid), "pid": pid, "error": str(exc)}

def get_system_status():
    status = {
        "hostname": "AlonsoRTOS",
        "system": "MAGI SYSTEM v2.0",
        "kernel": "Linux 6.18.34+rpt-rpi-v8-rt SMP PREEMPT_RT",
        "core_domain": "Core 1 (UI / Touch / Audio / Agent)",
        "cpu_temp": 50.0,
        "ram_used_mb": 400,
        "ram_total_mb": 15360,
        "wifi_connected": False,
        "wifi_ssid": "ETH0 DIRECT LINK",
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

@app.route("/api/magi/prompt", methods=["POST"])
def api_magi_prompt():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()
    
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"success": False, "error": "Prompt vacio"}), 400

    print(f"[+] MAGI PROMPT RECEIVED (Core 1): {prompt}")
    primary = _command_result(
        ["taskset", "-c", "1", "agy", "-p", prompt],
        AGY_TIMEOUT_SECONDS, env=_agy_environment()
    )
    summary, summary_result = _summarize_for_tts(prompt, primary)
    success = primary["returncode"] == 0 and bool(primary["stdout"]) and not primary["timed_out"]
    response = {
        "success": success,
        "output": primary["stdout"] if success else _failure_summary(primary),
        "summary": summary,
        "stdout": primary["stdout"],
        "stderr": primary["stderr"],
        "returncode": primary["returncode"],
        "execution_time_ms": primary["duration_ms"],
        "timed_out": primary["timed_out"],
        "summary_call": {
            "returncode": summary_result["returncode"],
            "stderr": summary_result["stderr"],
            "duration_ms": summary_result["duration_ms"],
            "timed_out": summary_result["timed_out"],
        },
        "core": "Core 1",
    }
    if success:
        return jsonify(response), 200
    return jsonify(response), (504 if primary["timed_out"] else 502)

@app.route("/api/audio/tts", methods=["POST"])
def api_audio_tts():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    text = data.get("text", "").strip()
    rate = data.get("rate", 1.6)
    pitch = data.get("pitch", 1.25)

    if not text:
        return jsonify({"success": False, "error": "Texto vacio"}), 400

    print(f"[+] MAGI TTS SYNTHESIS (Core 1): '{text}' [Rate: {rate}, Pitch: {pitch}]")

    try:
        tts_cmd = None
        for bin_name in ["espeak-ng", "espeak"]:
            res = subprocess.run(["which", bin_name], capture_output=True, text=True)
            if res.returncode == 0:
                tts_cmd = ["taskset", "-c", "1", bin_name, "-v", "f5", "-s", "175", "-p", "70", text]
                break

        if tts_cmd:
            subprocess.Popen(tts_cmd)
            return jsonify({"success": True, "engine": tts_cmd[2], "text": text})
        else:
            return jsonify({"success": True, "engine": "web_speech_api_proxy", "text": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/wifi/scan")
def api_wifi_scan():
    networks = []
    res = _command_result(
        ["nmcli", "--terse", "--escape", "yes", "--fields", "SSID,SIGNAL,SECURITY,CHAN,RATE",
         "device", "wifi", "list", "--rescan", "auto"],
        NETWORK_TIMEOUT_SECONDS
    )
    if res["timed_out"]:
        return jsonify({"success": False, "error": "nmcli scan timeout", "details": res, "networks": []}), 504
    if res["returncode"] != 0:
        return jsonify({"success": False, "error": res["stderr"] or res["stdout"], "details": res, "networks": []}), 502
    try:
        seen_ssids = set()
        for line in res["stdout"].splitlines():
            if not line:
                continue
            parts = _split_nmcli_line(line)
            if len(parts) == 5 and parts[0]:
                ssid = parts[0]
                if ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    networks.append({
                        "ssid": ssid,
                        "signal": int(parts[1]) if parts[1].isdigit() else 0,
                        "security": parts[2] if parts[2] else "Open",
                        "channel": parts[3],
                        "rate": parts[4]
                    })
        networks.sort(key=lambda x: x["signal"], reverse=True)
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid nmcli output: {e}", "details": res, "networks": []}), 502

    return jsonify({"success": True, "networks": networks})

@app.route("/api/wifi/connect", methods=["POST"])
def api_wifi_connect():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()

    if not ssid:
        return jsonify({"success": False, "message": "SSID no especificado"}), 400

    cmd = ["nmcli", "device", "wifi", "connect", ssid]
    if password:
        cmd.extend(["password", password])
    res = _command_result(cmd, NETWORK_TIMEOUT_SECONDS)
    if res["timed_out"]:
        return jsonify({"success": False, "message": "Tiempo de espera agotado al autenticar red", "details": res}), 504
    if res["returncode"] != 0:
        return jsonify({"success": False, "message": res["stderr"] or res["stdout"], "details": res}), 502
    return jsonify({"success": True, "message": f"Conectado a {ssid}", "output": res["stdout"], "details": res})

@app.route("/api/wifi/disconnect", methods=["POST"])
def api_wifi_disconnect():
    device = (request.get_json(silent=True) or {}).get("device", "wlan0")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", device):
        return jsonify({"success": False, "message": "Interfaz Wi-Fi invalida"}), 400
    res = _command_result(["nmcli", "device", "disconnect", device], NETWORK_TIMEOUT_SECONDS)
    if res["timed_out"]:
        return jsonify({"success": False, "message": "nmcli disconnect timeout", "details": res}), 504
    if res["returncode"] != 0:
        return jsonify({"success": False, "message": res["stderr"] or res["stdout"], "details": res}), 502
    return jsonify({"success": True, "message": "Interfaz Wi-Fi desconectada", "details": res})

@app.route("/api/bluetooth/scan")
def api_bluetooth_scan():
    power = _bluetoothctl("power on")
    if power["returncode"] != 0 or power["timed_out"]:
        return jsonify({"success": False, "error": power["stderr"] or power["stdout"] or "No se pudo activar Bluetooth", "details": power, "devices": []}), (504 if power["timed_out"] else 502)
    discovery = _command_result(
        ["bluetoothctl", "--timeout", str(max(1, int(BLUETOOTH_TIMEOUT_SECONDS))), "scan", "on"],
        BLUETOOTH_TIMEOUT_SECONDS + 2
    )
    if discovery["timed_out"]:
        return jsonify({"success": False, "error": "Bluetooth discovery timeout", "details": discovery, "devices": []}), 504
    if discovery["returncode"] != 0:
        return jsonify({"success": False, "error": discovery["stderr"] or discovery["stdout"], "details": discovery, "devices": []}), 502
    listing = _command_result(["bluetoothctl", "devices"], BLUETOOTH_TIMEOUT_SECONDS)
    if listing["returncode"] != 0 or listing["timed_out"]:
        return jsonify({"success": False, "error": listing["stderr"] or listing["stdout"] or "No se pudieron listar dispositivos", "details": listing, "devices": []}), (504 if listing["timed_out"] else 502)
    found = {}
    for line in (discovery["stdout"] + "\n" + listing["stdout"]).splitlines():
        match = re.search(r"(?:^|\s)Device\s+((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})(?:\s+(.*))?$", line)
        if match:
            found[match.group(1).upper()] = (match.group(2) or match.group(1)).strip()
    devices = []
    for mac, discovered_name in found.items():
        info_result, properties = _bluetooth_info(mac)
        devices.append({
            "mac": mac,
            "name": properties.get("name", properties.get("alias", discovered_name)),
            "paired": properties.get("paired", "no").lower() == "yes",
            "trusted": properties.get("trusted", "no").lower() == "yes",
            "connected": properties.get("connected", "no").lower() == "yes",
            "info_error": None if info_result["returncode"] == 0 else (info_result["stderr"] or info_result["stdout"]),
        })
    return jsonify({"success": True, "devices": devices, "details": {"discovery": discovery, "listing": listing}})


@app.route("/api/bluetooth/<action>", methods=["POST"])
def api_bluetooth_action(action):
    if action not in {"pair", "trust", "connect", "disconnect"}:
        return jsonify({"success": False, "error": "Accion Bluetooth no soportada"}), 404
    data = request.get_json(silent=True) or {}
    mac = str(data.get("mac", "")).upper()
    if not BLUETOOTH_MAC_RE.fullmatch(mac):
        return jsonify({"success": False, "error": "Direccion Bluetooth invalida"}), 400
    result = _bluetoothctl("power on", f"{action} {mac}")
    if result["timed_out"]:
        return jsonify({"success": False, "error": f"Bluetooth {action} timeout", "details": result}), 504
    info_result, properties = _bluetooth_info(mac)
    expected_property = {"pair": "paired", "trust": "trusted", "connect": "connected", "disconnect": "connected"}[action]
    expected_value = action != "disconnect"
    observed_value = properties.get(expected_property, "no").lower() == "yes"
    verified = info_result["returncode"] == 0 and observed_value == expected_value
    success = result["returncode"] == 0 and verified
    payload = {
        "success": success, "action": action, "mac": mac, "verified": verified,
        "state": {"paired": properties.get("paired"), "trusted": properties.get("trusted"),
                  "connected": properties.get("connected")},
        "details": result, "verification": info_result,
    }
    if success:
        return jsonify(payload), 200
    payload["error"] = result["stderr"] or result["stdout"] or info_result["stderr"] or "Estado Bluetooth no verificado"
    return jsonify(payload), 502


@app.route("/api/osk/<action>", methods=["GET", "POST"])
def api_osk_action(action):
    if action not in {"show", "hide", "status"}:
        return jsonify({"success": False, "error": "Accion OSK no soportada"}), 404
    if request.method == "GET" and action != "status":
        return jsonify({"success": False, "error": "show/hide requieren POST"}), 405
    if not _request_is_local(request.remote_addr, request.headers.get("Origin")):
        return jsonify({"success": False, "error": "Solicitud OSK rechazada: origen no autorizado"}), 403
    with _osk_lock:
        if action == "show":
            result = _show_osk()
        elif action == "hide":
            result = _hide_osk()
        else:
            pid = _current_osk_pid()
            result = {"success": True, "running": pid is not None, "pid": pid}
    return jsonify(result), (200 if result["success"] else 500)

@app.route("/api/hil/command", methods=["POST"])
def api_hil_command():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    action_id = data.get("action_id", 1)
    target_speed = float(data.get("speed", 0.0))
    flags = data.get("flags", 1) # CTRL_FLAG_MOTOR_ENABLE

    payload = json.dumps({"action_id": action_id, "speed": target_speed, "flags": flags})
    try:
        subprocess.run(["mosquitto_pub", "-t", "hil/command", "-m", payload], timeout=1)
        return jsonify({"success": True, "command_sent": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("[+] MAGI SYSTEM Server iniciando en Core 1 (0.0.0.0:8080)...")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
