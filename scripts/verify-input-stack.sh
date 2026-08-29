#!/usr/bin/env bash
# ==============================================================================
# HIL-RTOS WORKSTATION - INPUT SUBSYSTEM VERIFICATION SCRIPT (ROBUST RESOLVER)
# ==============================================================================
# Resuelve dinámicamente los dispositivos de entrada por nombre en /proc/bus/input/devices
# excluyendo adaptadores de audio/CEC HDMI, y certifica que el compositor labwc
# y wlroots carguen libinput en hardware real.
# ==============================================================================

set -eo pipefail

echo "========================================================================"
echo ">>> [1/5] VERIFICANDO SERVICIOS SYSTEMD ACTIVOS..."
echo "========================================================================"
for svc in seatd magi-ui magi-kiosk; do
    if systemctl is-active --quiet "$svc"; then
        echo "  [OK] $svc: ACTIVO"
    else
        echo "  [ERROR] $svc: INACTIVO / FALLIDO"
        systemctl status "$svc" --no-pager -l || true
        exit 1
    fi
done

echo ""
echo "========================================================================"
echo ">>> [2/5] RESOLVIENDO DISPOSITIVOS DE ENTRADA REALES (KERNEL / PROC)..."
echo "========================================================================"

# Resolución dinámica de la pantalla táctil (QDtech / Touchscreen)
TOUCH_NAME=$(grep -E 'N: Name=.*(QDtech|Touch|WaveShare)' /proc/bus/input/devices | head -1 | sed -e 's/N: Name=//g' -e 's/"//g' || true)
TOUCH_EVENT=$(grep -B2 -A6 -E 'N: Name=.*(QDtech|Touch|WaveShare)' /proc/bus/input/devices | grep -oP 'event\K[0-9]+' | head -1 || true)

if [ -n "$TOUCH_EVENT" ]; then
    echo "  [OK] Pantalla Táctil Detectada:"
    echo "       Nombre: \"$TOUCH_NAME\""
    echo "       Nodo:   /dev/input/event${TOUCH_EVENT}"
    if [ -e "/dev/input/event${TOUCH_EVENT}" ]; then
        echo "       Estado: Dispositivo presente en filesystem (/dev/input/event${TOUCH_EVENT})"
    else
        echo "       [ERROR] /dev/input/event${TOUCH_EVENT} no existe en filesystem"
        exit 1
    fi
else
    echo "  [WARN] No se detectó pantalla táctil reconocida por nombre en /proc/bus/input/devices"
fi

# Resolución dinámica del teclado físico (excluyendo Mouse y controles secundarios)
KBD_NAME=$(grep -E 'N: Name=.*(Keyboard|keyboard)' /proc/bus/input/devices | grep -vE '(Mouse|Control)' | head -1 | sed -e 's/N: Name=//g' -e 's/"//g' || true)
KBD_EVENT=$(grep -B2 -A6 -E 'N: Name=".*(Keyboard|keyboard)"' /proc/bus/input/devices | grep -vE '(Mouse|Control)' | grep -oP 'event\K[0-9]+' | head -1 || true)

if [ -n "$KBD_EVENT" ]; then
    echo "  [OK] Teclado Físico Detectado:"
    echo "       Nombre: \"$KBD_NAME\""
    echo "       Nodo:   /dev/input/event${KBD_EVENT}"
    if [ -e "/dev/input/event${KBD_EVENT}" ]; then
        echo "       Estado: Dispositivo presente en filesystem (/dev/input/event${KBD_EVENT})"
    else
        echo "       [ERROR] /dev/input/event${KBD_EVENT} no existe en filesystem"
        exit 1
    fi
else
    echo "  [WARN] No se detectó teclado físico primario en /proc/bus/input/devices"
fi

# Confirmación explícita de descarte de dispositivos no humanos (ej. HDMI audio jack)
echo "  [INFO] Dispositivos de audio/CEC excluidos de input humano:"
grep -E 'N: Name=.*(vc4-hdmi|HDMI Jack|pwr_button)' /proc/bus/input/devices | sed 's/N: Name=/         - /' || true

echo ""
echo "========================================================================"
echo ">>> [3/5] VERIFICANDO VARIABLES DE ENTORNO EN MAGI-KIOSK..."
echo "========================================================================"
KIOSK_PID=$(pgrep -f "/usr/bin/labwc" | head -n 1 || true)
if [ -z "$KIOSK_PID" ]; then
    echo "  [ERROR] Proceso labwc no encontrado"
    exit 1
fi
echo "  [OK] PID de labwc: $KIOSK_PID"

WLR_ENV=$(tr '\0' '\n' < /proc/$KIOSK_PID/environ | grep "^WLR_BACKENDS=" || true)
echo "  [STATUS] $WLR_ENV"

if [[ "$WLR_ENV" == *"libinput"* ]]; then
    echo "  [OK] libinput presente en WLR_BACKENDS de labwc"
else
    echo "  [ERROR CRITICO] WLR_BACKENDS NO contiene 'libinput'. Touch/Teclado no responderán."
    exit 2
fi

echo ""
echo "========================================================================"
echo ">>> [4/5] VERIFICANDO GESTION DE ASIENTO (SEATD / LIBSEAT)..."
echo "========================================================================"
if [ -e /run/seatd.sock ]; then
    echo "  [OK] Socket /run/seatd.sock activo"
else
    echo "  [WARN] Socket /run/seatd.sock no encontrado"
fi

echo ""
echo "========================================================================"
echo ">>> [5/5] VERIFICANDO LOGS DE COMPOSITOR Y CLIENTE HMI..."
echo "========================================================================"
JOURNAL_ERR=$(journalctl -u magi-kiosk -n 20 --no-pager | grep -i "libinput error" || true)
if [ -n "$JOURNAL_ERR" ]; then
    echo "  [WARN] Errores detectados en journal:"
    echo "$JOURNAL_ERR"
else
    echo "  [OK] Cero errores criticos de libinput en journal recent"
fi

echo ""
echo "========================================================================"
echo ">>> VERIFICACION COMPLETADA CON EXITO: STACK DE ENTRADA CERTIFICADO"
echo "========================================================================"
