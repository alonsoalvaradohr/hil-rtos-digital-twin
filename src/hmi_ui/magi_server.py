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
import selectors
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
NM_UUID_RE = re.compile(r"^[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}$")
NETWORK_DEVICE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
MAGI_MAX_PROMPT_LENGTH = int(os.environ.get("MAGI_MAX_PROMPT_LENGTH", "4000"))
OSK_EXECUTABLE = "/usr/bin/wvkbd-mobintl"
OSK_ENVIRONMENT = {"XDG_RUNTIME_DIR": "/run/user/1000", "WAYLAND_DISPLAY": "wayland-0"}
OSK_ALLOWED_ORIGINS = {"http://127.0.0.1:8080", "http://localhost:8080"}
_osk_lock = threading.Lock()
_osk_process = None
_osk_pid = None
_bluetooth_pair_lock = threading.Lock()

BLUETOOTH_ERROR_CODES = (
    "AuthenticationRejected", "AuthenticationCanceled", "AuthenticationFailed",
    "AuthenticationTimeout", "ConnectionAttemptFailed", "InProgress",
)


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


def _result_succeeded(result):
    return result["returncode"] == 0 and bool(result["stdout"]) and not result["timed_out"]


def _safe_error_line(stderr):
    """Reduce un error a una línea acotada y elimina marcadores/datos sensibles comunes."""
    line = next((part.strip() for part in (stderr or "").splitlines() if part.strip()), "sin detalle seguro")
    line = re.sub(r"(?i)\b(raw|secret|trace(?:back)?)\b", "[redacted]", line)
    line = re.sub(
        r"(?i)\b(password|passwd|token|api[_-]?key|authorization)\s*[:=]\s*[^\s,;]+",
        lambda match: f"{match.group(1)}=[redacted]", line
    )
    return line[:160]


def _failure_summary(result):
    if result["timed_out"]:
        return "La deliberacion excedio el tiempo permitido; no se obtuvo una conclusion verificable."
    return f"La deliberacion fallo con codigo {result['returncode']}. Detalle: {_safe_error_line(result['stderr'])}."


def _agy_environment():
    env = os.environ.copy()
    env["PATH"] = "/home/alonso/.local/bin:/usr/local/bin:" + env.get("PATH", "")
    return env


MAGI_PODS = (
    ("melchior", "MELCHIOR-1", "cientifico y factual", "Distingue hechos, inferencias e incognitas; exige evidencia reproducible."),
    ("balthasar", "BALTHASAR-2", "logico y pragmatico", "Evalua viabilidad y propone un plan atomico verificable con rollback."),
    ("casper", "CASPER-3", "humanista y esceptico", "Busca riesgos humanos, supuestos ocultos y emite veto de seguridad cuando corresponda."),
)


def _pod_prompt(key, name, persona, directive, user_prompt):
    scope = "Esta llamada es estrictamente no operativa: no ejecutes acciones ni herramientas externas."
    return (
        f"Eres {name}, pod MAGI {persona}. {directive} {scope} No inventes votos de otros pods ni declares "
        "consenso. Responde con POSICION, ARGUMENTOS, EVIDENCIA, RIESGOS, INCERTIDUMBRES y CONDICIONES O VETO. "
        "EVIDENCIA debe contener una URL valida, una ruta concreta, una tripleta COMANDO:`...` + "
        "SALIDA/STDOUT/STDERR no trivial + RC/EXIT CODE entero, o una medicion contextual con unidad. "
        "Un token generico como output/referencia/cita no es evidencia. Usa SIN EVIDENCIA SUFICIENTE cuando corresponda.\n"
        f"DIRECTIVA ORIGINAL:\n{user_prompt}"
    )


def _executor_prompt(user_prompt, golden_result):
    return (
        "Eres BALTHASAR-EXECUTOR. Esta es la unica llamada operativa y estas explicitamente autorizado a "
        "ejecutar las acciones y herramientas necesarias dentro del alcance aprobado por el Golden Path. "
        "No excedas ese alcance. Reporta resultado real, comandos, stdout/stderr, errores y rollback; no "
        "inventes éxito.\n"
        f"DIRECTIVA ORIGINAL:\n{user_prompt}\n"
        f"GOLDEN PATH VALIDADO:\n{golden_result['stdout']}"
    )


def _extract_position(text):
    match = re.search(r"(?im)^\s*POSICI[ÓO]N\s*:\s*([^\r\n]+)", text or "")
    return match.group(1).strip()[:120] if match else "NO DECLARADA"


POD_SECTION_PATTERN = re.compile(
    r"(?ims)^\s*(POSICI[ÓO]N|ARGUMENTOS|EVIDENCIA|RIESGOS|INCERTIDUMBRES|CONDICIONES O VETO)\s*:\s*"
    r"(.*?)(?=^\s*(?:POSICI[ÓO]N|ARGUMENTOS|EVIDENCIA|RIESGOS|INCERTIDUMBRES|CONDICIONES O VETO)\s*:|\Z)"
)
POD_POSITIONS = {"APROBAR", "APROBAR CON CONDICIONES", "RECHAZAR", "SIN EVIDENCIA SUFICIENTE"}
GOLDEN_SECTIONS = ("DECISION", "GOLDEN PATH", "DISENSO", "VETOS", "EVIDENCIA", "PENDIENTES")
GOLDEN_DECISIONS = {"EJECUTAR", "EJECUTAR CON CONDICIONES", "NO EJECUTAR", "SIN EVIDENCIA SUFICIENTE"}


def _parse_sections(text, pattern):
    sections = {}
    for match in pattern.finditer(text or ""):
        key = match.group(1).upper().replace("Ó", "O")
        sections[key] = match.group(2).strip()
    return sections


def _section_is_nontrivial(value):
    normalized = re.sub(r"\s+", " ", value or "").strip()
    return len(normalized) >= 4 and normalized.lower() not in {"-", "x", "n/a", "na", "none", "null"} and not normalized.isdigit()


def _evidence_is_concrete(evidence):
    if "SIN EVIDENCIA SUFICIENTE" in evidence.upper():
        return False
    text = evidence.strip()
    if len(text) < 20:
        return False
    for candidate in re.findall(r"https?://[^\s<>()]+", text, flags=re.IGNORECASE):
        parsed = urlsplit(candidate.rstrip(".,;"))
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return True
    concrete_path = re.search(
        r"(?i)(?:^|\s)(?:/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+|"
        r"(?:\./|\.\./)[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+|"
        r"[A-Za-z]:\\[A-Za-z0-9._ -]+(?:\\[A-Za-z0-9._ -]+)+)(?=$|[\s,;:])",
        text
    )
    if concrete_path:
        return True
    command = re.search(r"(?is)\bCOMANDO\s*:\s*`[^`\r\n]+`", text)
    material_output = re.search(
        r"(?is)\b(?:SALIDA|STDOUT|STDERR)\s*:\s*(?!\s*(?:-|x|n/?a)\s*(?:$|[;,]))(.{4,}?)"
        r"(?=\s+(?:RC|EXIT\s+CODE)\s*[:=]|$)", text
    )
    return_code = re.search(r"(?i)\b(?:RC|EXIT\s+CODE)\s*[:=]\s*-?\d+\b", text)
    if command and material_output and return_code:
        return True
    measurement = re.search(
        r"(?i)\b\d+(?:[.,]\d+)?\s*(?:ns|us|µs|ms|s|hz|khz|mhz|ghz|%|bytes?|kb|mb|gb|°c|v|a|w)\b",
        text
    )
    return bool(measurement)


def _validate_pod_result(result):
    errors = []
    sections = _parse_sections(result["stdout"], POD_SECTION_PATTERN)
    required = ("POSICION", "ARGUMENTOS", "EVIDENCIA", "RIESGOS", "INCERTIDUMBRES", "CONDICIONES O VETO")
    for name in required:
        if not _section_is_nontrivial(sections.get(name)):
            errors.append(f"Seccion ausente, vacia o trivial: {name}")
    position = sections.get("POSICION", "NO DECLARADA").upper()
    if position not in POD_POSITIONS:
        errors.append(f"POSICION invalida: {position}")
    evidence = sections.get("EVIDENCIA", "")
    evidence_sufficient = _evidence_is_concrete(evidence) and position != "SIN EVIDENCIA SUFICIENTE"
    if evidence and not evidence_sufficient and "SIN EVIDENCIA SUFICIENTE" not in evidence.upper():
        errors.append("EVIDENCIA no contiene una referencia concreta ni declara SIN EVIDENCIA SUFICIENTE")
    return {"valid": not errors, "position": position, "sections": sections,
            "evidence_sufficient": evidence_sufficient, "validation_errors": errors}


def _validate_golden_result(result):
    heading = "|".join(re.escape(name) for name in GOLDEN_SECTIONS)
    pattern = re.compile(rf"(?ims)^\s*({heading})\s*:\s*(.*?)(?=^\s*(?:{heading})\s*:|\Z)")
    sections = _parse_sections(result["stdout"], pattern)
    errors = [f"Seccion ausente, vacia o trivial: {name}" for name in GOLDEN_SECTIONS
              if not _section_is_nontrivial(sections.get(name))]
    decision = sections.get("DECISION", "").upper()
    if decision not in GOLDEN_DECISIONS:
        errors.append(f"DECISION invalida: {decision}")
    evidence = sections.get("EVIDENCIA", "")
    evidence_sufficient = _evidence_is_concrete(evidence) and decision != "SIN EVIDENCIA SUFICIENTE"
    if evidence and not evidence_sufficient and "SIN EVIDENCIA SUFICIENTE" not in evidence.upper():
        errors.append("EVIDENCIA de Golden Path no es concreta")
    return {"valid": _result_succeeded(result) and not errors, "sections": sections,
            "evidence_sufficient": evidence_sufficient, "validation_errors": errors}


def _golden_allows_execution(validation):
    decision = validation["sections"].get("DECISION", "").upper()
    return validation["valid"] and validation["evidence_sufficient"] and decision in {"EJECUTAR", "EJECUTAR CON CONDICIONES"}


def _golden_path_prompt(pods):
    evidence = [{"pod": pod["name"], "result": pod["result"]} for pod in pods]
    return (
        "TAREA ESTRICTAMENTE NO OPERATIVA. Sintetiza un Golden Path exclusivamente desde los dictamenes "
        "JSON siguientes. No ejecutes comandos ni herramientas. Conserva todo disenso y veto, no inventes "
        "consenso ni evidencia y responde con DECISION, GOLDEN PATH, DISENSO, VETOS, EVIDENCIA y PENDIENTES. "
        "EVIDENCIA debe usar URL valida, ruta concreta, tripleta COMANDO/SALIDA/RC o medicion contextual con unidad; "
        "tokens aislados output/referencia/cita no bastan. Si un pod fallo o falta evidencia critica, declara "
        "SIN EVIDENCIA SUFICIENTE.\n"
        + json.dumps(evidence, ensure_ascii=False)
    )


def _bounded_process_text(value, limit=1200):
    text = re.sub(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", value or "")
    text = "".join(char for char in text if char in "\n\t" or (ord(char) >= 32 and not 127 <= ord(char) <= 159))
    if len(text) <= limit:
        return text
    half = (limit - len("\n[...TRUNCADO...]\n")) // 2
    return text[:half] + "\n[...TRUNCADO...]\n" + text[-half:]


def _spoken_summary_prompt(consensus, golden_result, execution_result):
    execution = None if execution_result is None else {
        "returncode": execution_result["returncode"],
        "timed_out": execution_result["timed_out"],
        "duration_ms": execution_result["duration_ms"],
        "stdout": _bounded_process_text(execution_result["stdout"]),
        "stderr": _bounded_process_text(execution_result["stderr"]),
    }
    oral_input = {
        "consensus_status": consensus["status"],
        "consensus_reached": consensus["reached"],
        "vetoes": consensus["vetoes"],
        "golden_path": golden_result["stdout"] if _result_succeeded(golden_result) else None,
        "golden_path_returncode": golden_result["returncode"],
        "golden_path_timed_out": golden_result["timed_out"],
        "balthasar_executor": execution,
    }
    return (
        "TAREA ESTRICTAMENTE NO OPERATIVA Y SIN HERRAMIENTAS. Redacta un resumen oral natural en espanol "
        "de 1 a 3 frases y maximo 600 caracteres usando solo el JSON siguiente. Menciona el estado, los vetos "
        "y la recomendacion principal disponible. Resume el resultado real del ejecutor, incluidos sus fallos, "
        "sin recitar logs, trazas ni bloques de codigo "
        "ni afirmes consenso cuando consensus_reached sea false. Responde solamente con el texto para TTS.\n"
        + json.dumps(oral_input, ensure_ascii=False)
    )


def _validate_spoken_summary(result):
    if not _result_succeeded(result):
        return None, "La llamada de resumen oral fallo o no produjo texto"
    text = re.sub(r"\s+", " ", result["stdout"]).strip()
    if not text:
        return None, "La llamada de resumen oral produjo texto vacio"
    if len(text) > 600:
        return None, "La llamada de resumen oral excedio 600 caracteres"
    return text, None


def _spoken_summary_fallback(consensus, pods, golden_result, summary_result):
    status = consensus["status"].lower()
    veto_text = f" Se registraron vetos de {', '.join(consensus['vetoes'])}." if consensus["vetoes"] else " No se registraron vetos explicitos."
    failed_pods = sum(1 for pod in pods if not pod["success"])
    timeout_seen = any(pod["result"]["timed_out"] for pod in pods) or golden_result["timed_out"] or summary_result["timed_out"]
    rc = summary_result["returncode"]
    detail = " Hubo al menos un timeout." if timeout_seen else (f" El resumen oral fallo con codigo {rc}." if rc is not None else " El resumen oral no estuvo disponible.")
    pod_text = f" {failed_pods} dictamenes no finalizaron correctamente." if failed_pods else ""
    return f"La deliberacion termino con estado {status}.{veto_text}{pod_text}{detail}"[:600]


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


def _valid_network_device(device):
    return isinstance(device, str) and bool(NETWORK_DEVICE_RE.fullmatch(device))


def _nmcli_active_uuid(device):
    result = _command_result(
        ["nmcli", "--get-values", "GENERAL.CON-UUID", "device", "show", device],
        NETWORK_TIMEOUT_SECONDS
    )
    value = result["stdout"].strip()
    return (value.lower() if NM_UUID_RE.fullmatch(value) else None), result


def _wifi_profile_properties(uuid):
    if not NM_UUID_RE.fullmatch(uuid or ""):
        return None, {"returncode": None, "stdout": "", "stderr": "UUID invalido", "duration_ms": 0, "timed_out": False}
    result = _command_result(
        ["nmcli", "--terse", "--escape", "yes", "--get-values",
         "connection.id,connection.uuid,802-11-wireless.ssid,connection.autoconnect,connection.autoconnect-priority",
         "connection", "show", "uuid", uuid],
        NETWORK_TIMEOUT_SECONDS
    )
    if result["returncode"] != 0 or result["timed_out"]:
        return None, result
    lines = result["stdout"].splitlines()
    if len(lines) != 5:
        result["stderr"] = result["stderr"] or f"Salida nmcli inesperada: {len(lines)} campos"
        return None, result
    unescape = lambda value: ":".join(_split_nmcli_line(value))
    try:
        priority = int(lines[4])
    except ValueError:
        priority = 0
    return {
        "name": unescape(lines[0]), "uuid": lines[1].lower(), "ssid": unescape(lines[2]),
        "autoconnect": lines[3].strip().lower() == "yes", "priority": priority,
    }, result


def _known_wifi_profiles():
    listing = _command_result(
        ["nmcli", "--terse", "--escape", "yes", "--fields", "UUID,TYPE", "connection", "show"],
        NETWORK_TIMEOUT_SECONDS
    )
    if listing["returncode"] != 0 or listing["timed_out"]:
        return None, listing, []
    profiles, details = [], []
    for line in listing["stdout"].splitlines():
        parts = _split_nmcli_line(line)
        if len(parts) != 2 or parts[1] not in {"wifi", "802-11-wireless"} or not NM_UUID_RE.fullmatch(parts[0]):
            continue
        profile, result = _wifi_profile_properties(parts[0])
        details.append(result)
        if profile is not None:
            profiles.append(profile)
    profiles.sort(key=lambda profile: (-profile["priority"], profile["name"].casefold()))
    return profiles, listing, details


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


def _pairing_challenge(output):
    authorization = re.search(r"(?i)Authorize service\s+([0-9A-Fa-f-]{4,36})\s*\(yes/no\)", output)
    if authorization:
        return {"pairing_required": True, "challenge_type": "authorization",
                "passkey_display": None, "service_uuid": authorization.group(1)}
    confirmation = re.search(r"(?i)(?:confirm passkey|confirmation).*?([0-9]{6})", output)
    if confirmation:
        return {"pairing_required": True, "challenge_type": "confirmation",
                "passkey_display": confirmation.group(1)}
    display = re.search(r"(?i)(?:passkey|PIN code)\s*[:=]\s*([0-9]{4,6})", output)
    if display and not re.search(r"(?i)enter\s+(?:PIN|passkey)", output):
        return {"pairing_required": False, "challenge_type": "display",
                "passkey_display": display.group(1)}
    if re.search(r"(?i)enter\s+PIN", output):
        return {"pairing_required": True, "challenge_type": "pin",
                "passkey_display": None}
    if re.search(r"(?i)enter\s+passkey", output):
        return {"pairing_required": True, "challenge_type": "passkey",
                "passkey_display": None}
    return None


def _bluetooth_error_code(output):
    return next((code for code in BLUETOOTH_ERROR_CODES if code.lower() in output.lower()), None)


def _pairing_response(challenge, passkey, confirm):
    if challenge["challenge_type"] in {"pin", "passkey"}:
        return passkey if passkey is not None else None
    if challenge["challenge_type"] in {"confirmation", "authorization"}:
        return ("yes" if confirm else "no") if confirm is not None else None
    return None


def _bluetooth_pair_transaction(mac, passkey=None, confirm=None, timeout=BLUETOOTH_TIMEOUT_SECONDS):
    """Mantiene un agente KeyboardDisplay activo y responde solo a desafíos observados."""
    started = time.monotonic()
    stdout_chunks, stderr_chunks = [], []
    try:
        process = subprocess.Popen(
            ["bluetoothctl", "--agent", "KeyboardDisplay"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
        )
    except OSError as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc), "duration_ms": 0,
                "timed_out": False, "pairing_required": False}

    def send(line):
        try:
            process.stdin.write((line + "\n").encode("utf-8"))
            process.stdin.flush()
            return True
        except OSError as exc:
            stderr_chunks.append(str(exc))
            if process.poll() is None:
                process.kill()
            return False

    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, stdout_chunks)
    selector.register(process.stderr, selectors.EVENT_READ, stderr_chunks)
    send("agent KeyboardDisplay")
    send("default-agent")
    send(f"pair {mac}")
    responded_to = set()
    followup_sent = False
    required = None
    observed_display = None
    timed_out = False
    try:
        while process.poll() is None:
            if time.monotonic() - started >= timeout:
                timed_out = True
                process.kill()
                break
            for key, _ in selector.select(timeout=0.1):
                chunk = os.read(key.fileobj.fileno(), 4096)
                if chunk:
                    key.data.append(chunk.decode("utf-8", errors="replace"))
            combined = "".join(stdout_chunks + stderr_chunks)
            challenge = _pairing_challenge(combined)
            if challenge:
                signature = (challenge["challenge_type"], challenge["passkey_display"])
                if signature not in responded_to:
                    responded_to.add(signature)
                    if not challenge["pairing_required"]:
                        observed_display = challenge
                        continue
                    response = _pairing_response(challenge, passkey, confirm)
                    if response is None:
                        required = challenge
                        process.terminate()
                        break
                    send(response)
            if not followup_sent and re.search(r"(?i)(pairing successful|already paired|AlreadyExists)", combined):
                send(f"trust {mac}")
                send(f"connect {mac}")
                send("quit")
                followup_sent = True
            elif not followup_sent and _bluetooth_error_code(combined):
                send("quit")
                followup_sent = True
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        for stream, chunks in ((process.stdout, stdout_chunks), (process.stderr, stderr_chunks)):
            remainder = stream.read()
            if remainder:
                chunks.append(remainder.decode("utf-8", errors="replace"))
    finally:
        selector.close()
    result = {
        "returncode": process.returncode, "stdout": "".join(stdout_chunks).strip(),
        "stderr": "".join(stderr_chunks).strip(),
        "duration_ms": round((time.monotonic() - started) * 1000, 1), "timed_out": timed_out,
        "pairing_required": required is not None,
    }
    if required:
        result.update(required)
    elif observed_display:
        result.update(observed_display)
    return result


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


def _require_local_request():
    if _request_is_local(request.remote_addr, request.headers.get("Origin")):
        return None
    return jsonify({"success": False, "error": "Solicitud rechazada: origen/cliente no autorizado"}), 403


def _pod_has_veto(pod):
    if pod["position"].upper().startswith("RECHAZAR"):
        return True
    for match in re.finditer(r"(?im)^\s*(?:CONDICIONES O VETO|VETO)\s*:\s*(.+)$", pod["result"]["stdout"]):
        value = match.group(1).strip().upper()
        if value and not re.match(r"^(?:NO|NINGUN[OA]?|SIN VETO)\b", value):
            return True
    return False


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
        "hostname": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME"),
        "system": "MAGI SYSTEM v2.0",
        "kernel": os.uname().release if hasattr(os, "uname") else None,
        "core_domain": "Core 1 (UI / Touch / Audio / Agent)",
        "cpu_temp": None,
        "ram_used_mb": None,
        "ram_total_mb": None,
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

        if hasattr(os, "sysconf"):
            page_size = os.sysconf("SC_PAGE_SIZE")
            total_pages = os.sysconf("SC_PHYS_PAGES")
            available_pages = os.sysconf("SC_AVPHYS_PAGES")
            status["ram_total_mb"] = round(page_size * total_pages / (1024 * 1024), 1)
            status["ram_used_mb"] = round(page_size * (total_pages - available_pages) / (1024 * 1024), 1)

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
    denied = _require_local_request()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()
    
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"success": False, "error": "Prompt vacio"}), 400
    if len(prompt) > MAGI_MAX_PROMPT_LENGTH:
        return jsonify({"success": False, "error": f"Prompt excede el limite de {MAGI_MAX_PROMPT_LENGTH} caracteres"}), 413

    print(f"[+] MAGI PROMPT RECEIVED (Core 1): {prompt}")
    pods = []
    for key, name, persona, directive in MAGI_PODS:
        result = _command_result(
            ["taskset", "-c", "1", "agy", "-p", _pod_prompt(key, name, persona, directive, prompt)],
            AGY_TIMEOUT_SECONDS, env=_agy_environment()
        )
        validation = _validate_pod_result(result) if _result_succeeded(result) else {
            "valid": False, "position": "SIN RESPUESTA", "sections": {}, "evidence_sufficient": False,
            "validation_errors": ["El proceso del pod fallo, expiro o no produjo salida"],
        }
        pods.append({"id": key, "name": name, "persona": persona,
                     "position": validation["position"], "success": _result_succeeded(result) and validation["valid"],
                     "evidence_sufficient": validation["evidence_sufficient"],
                     "validation_errors": validation["validation_errors"], "sections": validation["sections"],
                     "result": result})

    golden_result = _command_result(
        ["taskset", "-c", "1", "agy", "-p", _golden_path_prompt(pods)],
        AGY_SUMMARY_TIMEOUT_SECONDS, env=_agy_environment()
    )
    golden_validation = _validate_golden_result(golden_result)
    pods_succeeded = all(pod["success"] for pod in pods)
    golden_succeeded = golden_validation["valid"]
    deliberation_success = pods_succeeded and golden_succeeded
    vetoes = [pod["name"] for pod in pods if pod["success"] and _pod_has_veto(pod)]
    evidence_sufficient = all(pod["evidence_sufficient"] for pod in pods)
    all_evidence_sufficient = evidence_sufficient and golden_validation["evidence_sufficient"]
    positions_allow_execution = all(pod["position"] in {"APROBAR", "APROBAR CON CONDICIONES"} for pod in pods)
    execution_allowed = (deliberation_success and all_evidence_sufficient and positions_allow_execution
                         and not vetoes and _golden_allows_execution(golden_validation))
    execution_result = None
    execution_skipped_reason = None
    if execution_allowed:
        execution_result = _command_result(
            ["taskset", "-c", "1", "agy", "-p", _executor_prompt(prompt, golden_result)],
            AGY_TIMEOUT_SECONDS, env=_agy_environment()
        )
        execution_success = _result_succeeded(execution_result)
    else:
        execution_success = False
        if not deliberation_success:
            execution_skipped_reason = "Dictamenes o Golden Path invalidos"
        elif vetoes:
            execution_skipped_reason = "Veto de seguridad activo"
        elif not all_evidence_sufficient:
            execution_skipped_reason = "Evidencia insuficiente"
        elif not positions_allow_execution:
            execution_skipped_reason = "Las posiciones no autorizan ejecucion"
        else:
            execution_skipped_reason = "La decision del Golden Path no autoriza ejecucion"
    unanimous = (deliberation_success and all_evidence_sufficient and not vetoes and execution_success
                 and all(pod["position"] == "APROBAR" for pod in pods))
    consensus = {
        "reached": unanimous,
        "status": "CONSENSO" if unanimous else ("SIN EVIDENCIA SUFICIENTE" if not deliberation_success or not all_evidence_sufficient else "DISENSO"),
        "positions": {pod["name"]: pod["position"] for pod in pods},
        "vetoes": vetoes,
    }
    failed_result = next((pod["result"] for pod in pods if not pod["success"]), golden_result)
    fallback = _failure_summary(failed_result)
    summary_result = _command_result(
        ["taskset", "-c", "1", "agy", "-p", _spoken_summary_prompt(consensus, golden_result, execution_result)],
        AGY_SUMMARY_TIMEOUT_SECONDS, env=_agy_environment()
    )
    spoken_summary, summary_error = _validate_spoken_summary(summary_result)
    summary_degraded = spoken_summary is None
    if summary_degraded:
        spoken_summary = _spoken_summary_fallback(consensus, pods, golden_result, summary_result)
    summary_success = not summary_degraded
    execution_stage_success = execution_success if execution_allowed else execution_skipped_reason is not None
    pipeline_success = deliberation_success and execution_stage_success and summary_success
    response = {
        "request_processed": True,
        "success": pipeline_success,
        "pipeline_success": pipeline_success,
        "deliberation_success": deliberation_success,
        "execution_success": execution_success,
        "execution_result": execution_result,
        "execution_skipped_reason": execution_skipped_reason,
        "output": golden_result["stdout"] if golden_succeeded else fallback,
        "summary": spoken_summary,
        "summary_degraded": summary_degraded,
        "summary_error": summary_error,
        "summary_call": summary_result,
        "stdout": golden_result["stdout"],
        "stderr": golden_result["stderr"],
        "returncode": golden_result["returncode"],
        "execution_time_ms": (sum(pod["result"]["duration_ms"] for pod in pods) + golden_result["duration_ms"]
                              + (execution_result["duration_ms"] if execution_result else 0)),
        "summary_execution_time_ms": summary_result["duration_ms"],
        "timed_out": (any(pod["result"]["timed_out"] for pod in pods) or golden_result["timed_out"]
                      or bool(execution_result and execution_result["timed_out"])),
        "deliberation": {"pods": pods},
        "pods": pods,
        "golden_path": golden_result,
        "golden_path_validation": golden_validation,
        "consensus": consensus,
        "core": "Core 1",
    }
    if pipeline_success:
        return jsonify(response), 200
    return jsonify(response), (504 if response["timed_out"] else 502)

@app.route("/api/audio/tts", methods=["POST"])
def api_audio_tts():
    denied = _require_local_request()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    text = data.get("text", "").strip()
    rate = data.get("rate", 1.6)
    pitch = data.get("pitch", 1.25)

    if not text:
        return jsonify({"success": False, "error": "Texto vacio"}), 400

    try:
        speech_rate = max(100, min(400, int(float(rate) * 175)))
        speech_pitch = max(0, min(99, int(float(pitch) * 50)))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Rate o pitch invalidos"}), 400

    print(f"[+] MAGI TTS SYNTHESIS (Core 1): '{text}' [Rate: {speech_rate}, Pitch: {speech_pitch}]")

    try:
        tts_cmd = None
        for bin_name in ["espeak-ng", "espeak"]:
            res = subprocess.run(["which", bin_name], capture_output=True, text=True)
            if res.returncode == 0:
                # `es` is supplied by the Debian espeak-ng package and provides a
                # neutral synthetic Spanish voice without relying on optional MBROLA voices.
                tts_cmd = ["taskset", "-c", "1", bin_name, "-v", "es", "-s", str(speech_rate), "-p", str(speech_pitch), text]
                break

        if tts_cmd:
            process = subprocess.Popen(tts_cmd)
            time.sleep(0.05)
            returncode = process.poll()
            if returncode is not None and returncode != 0:
                return jsonify({"success": False, "error": f"TTS finalizo con codigo {returncode}", "returncode": returncode}), 502
            return jsonify({"success": True, "engine": bin_name, "text": text, "pid": process.pid})
        else:
            return jsonify({"success": False, "error": "No hay motor TTS backend disponible"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/wifi/scan")
def api_wifi_scan():
    denied = _require_local_request()
    if denied:
        return denied
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
    denied = _require_local_request()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()
    device = data.get("device", "wlan0").strip()

    if not ssid:
        return jsonify({"success": False, "message": "SSID no especificado"}), 400
    if not _valid_network_device(device):
        return jsonify({"success": False, "message": "Interfaz Wi-Fi invalida"}), 400

    cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", device]
    if password:
        cmd.extend(["password", password])
    res = _command_result(cmd, NETWORK_TIMEOUT_SECONDS)
    if res["timed_out"]:
        return jsonify({"success": False, "message": "Tiempo de espera agotado al autenticar red", "details": res}), 504
    if res["returncode"] != 0:
        return jsonify({"success": False, "message": res["stderr"] or res["stdout"], "details": res}), 502
    uuid, active_check = _nmcli_active_uuid(device)
    if uuid is None:
        return jsonify({"success": False, "link_connected": True, "autoconnect_verified": False,
                        "message": "Enlace establecido, pero no se obtuvo UUID activo valido",
                        "details": {"connect": res, "active_uuid": active_check}}), 502
    configure = _command_result(
        ["nmcli", "connection", "modify", "uuid", uuid,
         "connection.autoconnect", "yes", "connection.autoconnect-retries", "0"],
        NETWORK_TIMEOUT_SECONDS
    )
    if configure["timed_out"] or configure["returncode"] != 0:
        return jsonify({"success": False, "link_connected": True, "uuid": uuid,
                        "autoconnect_verified": False,
                        "message": configure["stderr"] or configure["stdout"] or "No se pudo configurar autoconnect",
                        "details": {"connect": res, "active_uuid": active_check, "configure": configure}}), (504 if configure["timed_out"] else 502)
    profile, verify = _wifi_profile_properties(uuid)
    final_uuid, final_check = _nmcli_active_uuid(device)
    autoconnect_verified = bool(profile and profile["autoconnect"] and final_uuid == uuid)
    if not autoconnect_verified:
        return jsonify({"success": False, "link_connected": final_uuid == uuid, "uuid": uuid,
                        "autoconnect_verified": False, "message": "Autoconnect no pudo verificarse",
                        "profile": profile,
                        "details": {"connect": res, "configure": configure, "verify": verify,
                                    "final_active_uuid": final_check}}), 502
    return jsonify({"success": True, "link_connected": True, "autoconnect_verified": True,
                    "uuid": uuid, "profile": profile, "message": f"Conectado a {ssid} con autoconnect verificado",
                    "details": {"connect": res, "configure": configure, "verify": verify,
                                "final_active_uuid": final_check}})


@app.route("/api/wifi/known")
def api_wifi_known():
    denied = _require_local_request()
    if denied:
        return denied
    profiles, listing, details = _known_wifi_profiles()
    if profiles is None:
        return jsonify({"success": False, "error": listing["stderr"] or listing["stdout"],
                        "profiles": [], "details": listing}), (504 if listing["timed_out"] else 502)
    if any(result["returncode"] != 0 or result["timed_out"] for result in details):
        return jsonify({"success": False, "error": "No se pudieron verificar todos los perfiles Wi-Fi",
                        "profiles": profiles, "details": {"listing": listing, "profiles": details}}), 502
    return jsonify({"success": True, "profiles": profiles, "details": {"listing": listing, "profiles": details}})


@app.route("/api/wifi/reconnect", methods=["POST"])
def api_wifi_reconnect():
    denied = _require_local_request()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    device = data.get("device", "wlan0").strip()
    if not _valid_network_device(device):
        return jsonify({"success": False, "error": "Interfaz Wi-Fi invalida"}), 400
    active_uuid, initial_check = _nmcli_active_uuid(device)
    if active_uuid is not None:
        return jsonify({"success": True, "already_connected": True, "verified": True,
                        "device": device, "uuid": active_uuid, "details": initial_check})
    profiles, listing, profile_details = _known_wifi_profiles()
    if profiles is None:
        return jsonify({"success": False, "error": listing["stderr"] or listing["stdout"],
                        "attempts": [], "details": listing}), (504 if listing["timed_out"] else 502)
    candidates = [profile for profile in profiles if profile["autoconnect"]]
    if not candidates:
        return jsonify({"success": False, "error": "No hay perfiles Wi-Fi conocidos con autoconnect habilitado",
                        "attempts": [], "details": {"listing": listing, "profiles": profile_details}}), 409
    attempts = []
    for profile in candidates:
        result = _command_result(
            ["nmcli", "connection", "up", "uuid", profile["uuid"], "ifname", device],
            NETWORK_TIMEOUT_SECONDS
        )
        verified_uuid, verification = _nmcli_active_uuid(device)
        verified = result["returncode"] == 0 and not result["timed_out"] and verified_uuid == profile["uuid"]
        attempts.append({"uuid": profile["uuid"], "priority": profile["priority"], "result": result,
                         "verification": verification, "verified": verified})
        if verified:
            return jsonify({"success": True, "already_connected": False, "verified": True,
                            "device": device, "uuid": verified_uuid, "profile": profile,
                            "attempts": attempts})
    timed_out = any(attempt["result"]["timed_out"] for attempt in attempts)
    return jsonify({"success": False, "verified": False,
                    "error": "Ningun perfil conocido pudo reconectarse y verificarse",
                    "attempts": attempts}), (504 if timed_out else 502)

@app.route("/api/wifi/disconnect", methods=["POST"])
def api_wifi_disconnect():
    denied = _require_local_request()
    if denied:
        return denied
    device = (request.get_json(silent=True) or {}).get("device", "wlan0")
    if not _valid_network_device(device):
        return jsonify({"success": False, "message": "Interfaz Wi-Fi invalida"}), 400
    res = _command_result(["nmcli", "device", "disconnect", device], NETWORK_TIMEOUT_SECONDS)
    if res["timed_out"]:
        return jsonify({"success": False, "message": "nmcli disconnect timeout", "details": res}), 504
    if res["returncode"] != 0:
        return jsonify({"success": False, "message": res["stderr"] or res["stdout"], "details": res}), 502
    return jsonify({"success": True, "message": "Interfaz Wi-Fi desconectada", "details": res})

@app.route("/api/bluetooth/scan")
def api_bluetooth_scan():
    denied = _require_local_request()
    if denied:
        return denied
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
    denied = _require_local_request()
    if denied:
        return denied
    if action not in {"pair", "trust", "connect", "disconnect"}:
        return jsonify({"success": False, "error": "Accion Bluetooth no soportada"}), 404
    data = request.get_json(silent=True) or {}
    mac = str(data.get("mac", "")).upper()
    if not BLUETOOTH_MAC_RE.fullmatch(mac):
        return jsonify({"success": False, "error": "Direccion Bluetooth invalida"}), 400
    passkey_value = data.get("passkey")
    passkey = None if passkey_value is None else str(passkey_value)
    if passkey is not None and (isinstance(passkey_value, bool) or not re.fullmatch(r"[0-9]{1,6}", passkey)
                                or not 0 <= int(passkey) <= 999999):
        return jsonify({"success": False, "error": "Passkey/PIN debe ser texto numerico entre 0 y 999999"}), 400
    confirm = data.get("confirm")
    if confirm is not None and not isinstance(confirm, bool):
        return jsonify({"success": False, "error": "confirm debe ser boolean"}), 400

    if action == "pair":
        with _bluetooth_pair_lock:
            result = _bluetooth_pair_transaction(mac, passkey=passkey, confirm=confirm)
            combined_output = result["stdout"] + "\n" + result["stderr"]
            error_code = _bluetooth_error_code(combined_output)
            if result.get("pairing_required"):
                return jsonify({
                    "success": False, "action": action, "mac": mac, "verified": False,
                    "pairing_required": True, "challenge_type": result.get("challenge_type"),
                    "passkey_display": result.get("passkey_display"), "service_uuid": result.get("service_uuid"),
                    "error_code": error_code,
                    "error": "BlueZ requiere respuesta explicita de pairing", "details": result,
                }), 409
            if result["timed_out"]:
                return jsonify({"success": False, "action": action, "mac": mac, "verified": False,
                                "pairing_required": False, "error_code": error_code or "AuthenticationTimeout",
                                "error": "Bluetooth pairing timeout", "details": result}), 504
            info_result, properties = _bluetooth_info(mac)
            state = {"paired": properties.get("paired", "no").lower() == "yes",
                     "trusted": properties.get("trusted", "no").lower() == "yes",
                     "connected": properties.get("connected", "no").lower() == "yes"}
            verified = info_result["returncode"] == 0 and all(state.values())
            success = result["returncode"] == 0 and verified and error_code is None
            payload = {"success": success, "action": action, "mac": mac, "verified": verified,
                       "pairing_required": False, "challenge_type": result.get("challenge_type"),
                       "passkey_display": result.get("passkey_display"), "error_code": error_code, "state": state,
                       "details": result, "verification": info_result}
            if success:
                return jsonify(payload), 200
            payload["error"] = error_code or result["stderr"] or result["stdout"] or info_result["stderr"] or "Pair/Trust/Connect no verificado"
            return jsonify(payload), 502

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
    denied = _require_local_request()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()

    action_id = data.get("action_id", 1)
    target_speed = float(data.get("speed", 0.0))
    flags = data.get("flags", 1) # CTRL_FLAG_MOTOR_ENABLE

    payload = json.dumps({"action_id": action_id, "speed": target_speed, "flags": flags})
    result = _command_result(["mosquitto_pub", "-t", "hil/command", "-m", payload], 1)
    if result["timed_out"]:
        return jsonify({"success": False, "error": "mosquitto_pub timeout", "details": result}), 504
    if result["returncode"] != 0:
        return jsonify({"success": False, "error": result["stderr"] or result["stdout"], "details": result}), 502
    return jsonify({"success": True, "command_sent": payload, "details": result})

if __name__ == "__main__":
    print("[+] MAGI SYSTEM Server iniciando en Core 1 (0.0.0.0:8080)...")
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
