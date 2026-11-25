#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
# HIL-RTOS INPUT SUBSYSTEM VERIFICATION (evidence-based, no inferred success)
# Usage: verify-input-stack.sh [--preflight|--certify|--certify-voice]
set -uo pipefail

MODE="${1:---preflight}"
PROC_ROOT="${HIL_PROC_ROOT:-/proc}"
FAILURES=0
PENDING=0

if [[ "$MODE" != "--preflight" && "$MODE" != "--certify" && "$MODE" != "--certify-voice" ]]; then
    echo "[ERROR] Modo inválido: $MODE"
    exit 64
fi

section() { echo "========================================================================"; echo ">>> $1"; echo "========================================================================"; }
fail() { echo "  [FAIL] $1"; FAILURES=$((FAILURES + 1)); }
run_literal() {
    echo "  \$ $*"
    "$@" 2>&1
    local rc=$?
    echo "  [exit=$rc]"
    return "$rc"
}

section "[1/7] SERVICIOS SYSTEMD"
for svc in seatd magi-ui magi-kiosk; do
    echo "  \$ systemctl is-active $svc"
    service_state=$(systemctl is-active "$svc" 2>&1); service_rc=$?
    printf '%s\n' "$service_state"; echo "  [exit=$service_rc]"
    if [[ $service_rc -ne 0 || "$service_state" != "active" ]]; then
        fail "$svc no está active"
        run_literal systemctl status "$svc" --no-pager -l || true
    fi
done

section "[2/7] DISPOSITIVOS DE ENTRADA"
INPUT_DEVICES="$PROC_ROOT/bus/input/devices"
echo "  \$ grep '^N: Name=' $INPUT_DEVICES"
if [[ -r "$INPUT_DEVICES" ]]; then
    grep '^N: Name=' "$INPUT_DEVICES" || true
    touch_line=$(grep -E 'N: Name=.*(QDtech|Touch|WaveShare)' "$INPUT_DEVICES" | head -n 1 || true)
    [[ -n "$touch_line" ]] || fail "No se detectó touchscreen reconocido en $INPUT_DEVICES"
else
    fail "No se puede leer $INPUT_DEVICES"
fi

section "[3/7] LABWC Y ENTORNO WLR"
echo "  \$ pgrep -x labwc"
labwc_pids=$(pgrep -x labwc 2>&1); labwc_rc=$?
printf '%s\n' "$labwc_pids"; echo "  [exit=$labwc_rc]"
labwc_count=$(printf '%s\n' "$labwc_pids" | awk 'NF {count++} END {print count+0}')
if [[ $labwc_rc -ne 0 || $labwc_count -ne 1 ]]; then
    fail "Se esperaba exactamente un proceso labwc; encontrados: $labwc_count"
else
    labwc_pid="$labwc_pids"; env_file="$PROC_ROOT/$labwc_pid/environ"
    echo "  \$ tr '\\0' '\\n' < $env_file"
    if [[ -r "$env_file" ]]; then
        env_output=$(tr '\0' '\n' < "$env_file"); printf '%s\n' "$env_output"
        wlr_count=$(printf '%s\n' "$env_output" | grep -c '^WLR_BACKENDS=' || true)
        wlr_value=$(printf '%s\n' "$env_output" | grep '^WLR_BACKENDS=' || true)
        [[ $wlr_count -eq 1 && "$wlr_value" == "WLR_BACKENDS=drm,libinput" ]] || fail "labwc debe contener exactamente WLR_BACKENDS=drm,libinput"
    else
        fail "No se puede leer $env_file"
    fi
fi

section "[4/7] CHROMIUM KIOSK ÚNICO"
chromium_pids=()
for cmdline_file in "$PROC_ROOT"/[0-9]*/cmdline; do
    [[ -r "$cmdline_file" ]] || continue
    cmdline=$(tr '\0' ' ' < "$cmdline_file"); first_arg=${cmdline%% *}; binary=${first_arg##*/}
    if [[ "$binary" =~ ^chromium(-browser)?$ && "$cmdline" == *" --kiosk "* && "$cmdline" == *"http://127.0.0.1:8080/"* ]]; then
        chromium_pids+=("$(basename "$(dirname "$cmdline_file")")")
    fi
done
printf '  Chromium kiosk PIDs:'; printf ' %s' "${chromium_pids[@]:-}"; printf '\n'
if [[ ${#chromium_pids[@]} -ne 1 ]]; then
    fail "Se esperaba exactamente una instancia Chromium kiosk relevante; encontradas: ${#chromium_pids[@]}"
else
    chromium_cmdline=$(tr '\0' ' ' < "$PROC_ROOT/${chromium_pids[0]}/cmdline")
    echo "  \$ tr '\\0' ' ' < $PROC_ROOT/${chromium_pids[0]}/cmdline"; printf '%s\n' "$chromium_cmdline"
    required_flags=("--kiosk" "--ozone-platform=wayland" "--user-data-dir=/tmp/chromium_magi_profile" "--use-fake-ui-for-media-stream" "--unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8080" "http://127.0.0.1:8080/")
    for expected in "${required_flags[@]}"; do
        [[ "$chromium_cmdline" == *"$expected"* ]] || fail "Chromium no contiene flag/origen esperado: $expected"
    done
fi

section "[5/7] JOURNAL DEL BOOT ACTUAL"
echo "  \$ journalctl -b -u magi-kiosk --no-pager"
journal_output=$(journalctl -b -u magi-kiosk --no-pager 2>&1); journal_rc=$?
printf '%s\n' "$journal_output"; echo "  [exit=$journal_rc]"
if [[ $journal_rc -ne 0 ]]; then
    fail "No se pudo consultar el journal del boot actual"
elif printf '%s\n' "$journal_output" | grep -Eiq 'libinput[^[:alnum:]]*(error|fatal)|(error|fatal)[^[:alnum:]]*libinput'; then
    fail "El journal contiene errores fatales o de libinput"
fi

section "[6/7] DEPENDENCIAS OPERATIVAS"
for tool in wvkbd-mobintl agy bluetoothctl nmcli; do
    echo "  \$ command -v $tool"
    tool_path=$(command -v "$tool" 2>&1); tool_rc=$?
    printf '%s\n' "$tool_path"; echo "  [exit=$tool_rc]"
    [[ $tool_rc -eq 0 && -n "$tool_path" ]] || fail "Dependencia ausente: $tool"
done

if [[ "$MODE" == "--certify-voice" ]]; then
    echo "  \$ arecord -l"
    mic_output=$(arecord -l 2>&1); mic_rc=$?
    printf '%s\n' "$mic_output"; echo "  [exit=$mic_rc]"
    if [[ $mic_rc -ne 0 ]] || ! printf '%s\n' "$mic_output" | grep -Eiq 'card [0-9]+:|CAPTURE'; then
        fail "No se detectó captura de audio; certificación de voz rechazada"
    fi
else
    echo "  [PENDIENTE] Use --certify-voice para comprobar captura de micrófono"
    PENDING=$((PENDING + 1))
fi

section "[7/7] VALIDACIÓN FÍSICA DEL OPERADOR"
echo "  [PENDIENTE] Confirmar toque, escritura ttyd, wvkbd y captura/reproducción de voz reales."
PENDING=$((PENDING + 1))
if [[ "$MODE" == "--certify" || "$MODE" == "--certify-voice" ]]; then
    if [[ "${HIL_OPERATOR_CONFIRMED:-}" != "yes" ]]; then
        fail "Certificación requiere HIL_OPERATOR_CONFIRMED=yes tras validación física"
    else
        echo "  HIL_OPERATOR_CONFIRMED=yes"
    fi
fi

section "RESULTADO"
echo "  MODO=$MODE"; echo "  FAILURES=$FAILURES"; echo "  PENDING=$PENDING"
if [[ $FAILURES -ne 0 ]]; then echo ">>> VERIFICACIÓN FALLIDA"; exit 1; fi
if [[ "$MODE" == "--preflight" ]]; then
    echo ">>> PREFLIGHT TÉCNICO APROBADO; VALIDACIONES FÍSICAS/VOZ SIGUEN PENDIENTES"
else
    echo ">>> CERTIFICACIÓN TÉCNICA APROBADA CON CONFIRMACIÓN DEL OPERADOR"
fi
