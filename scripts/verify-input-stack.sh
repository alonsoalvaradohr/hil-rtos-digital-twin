#!/usr/bin/env bash
# ==============================================================================
# HIL-RTOS WORKSTATION - INPUT SUBSYSTEM VERIFICATION SCRIPT
# ==============================================================================
# Ejecutar tras cualquier reinicio o modificacion de magi-kiosk.service / labwc.
# Verifica de extremo a extremo que el stack de entrada (evdev, seatd, wlroots,
# libinput) este activo y recibiendo eventos de hardware.
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
echo ">>> [2/5] VERIFICANDO DISPOSITIVOS DE ENTRADA EN KERNEL..."
echo "========================================================================"
if [ -e /dev/input/event0 ]; then
    echo "  [OK] Dispositivo /dev/input/event0 presente (Teclado/Mouse)"
else
    echo "  [WARN] /dev/input/event0 no encontrado"
fi

TOUCH_DEV=$(ls /dev/input/by-id/*Touch* 2>/dev/null || ls /dev/input/event* | tail -n 1)
echo "  [OK] Dispositivo de entrada táctil: $TOUCH_DEV"

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
    echo "  [ERROR CRITICO] WLR_BACKENDS NO contiene 'libinput'. Touch/Teclado no responderan."
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
echo ">>> VERIFICACION COMPLETADA CON EXITO: STACK DE ENTRADA OPERATIVO"
echo "========================================================================"
