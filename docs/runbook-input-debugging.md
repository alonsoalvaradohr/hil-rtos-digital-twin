# Runbook: Diagnóstico y Resolución del Subsistema de Entrada (HMI Kiosk / Wayland)

Este runbook documenta la secuencia atómica estricta de aislamiento por capas (Kernel → libinput/seatd → wlroots/labwc → Chromium HMI) para resolver incidencias donde la pantalla táctil o el teclado físico no responden en el kiosko.

---

## 1. Regla de Oro: Aislamiento de Abajo hacia Arriba
**Nunca modificar configuraciones del cliente (Chromium) o reglas complejas de udev sin haber validado cada una de las capas inferiores.**

```
+-------------------------------------------------------------+
| Capa 4: Cliente Wayland (Chromium / weston-terminal)       |
+-------------------------------------------------------------+
                              ^ (Protocolo Wayland: wl_seat)
+-------------------------------------------------------------+
| Capa 3: Compositor Wayland (labwc / wlroots)                |
+-------------------------------------------------------------+
                              ^ (libinput backend)
+-------------------------------------------------------------+
| Capa 2: Gestor de Asiento & libinput (seatd / libseat)      |
+-------------------------------------------------------------+
                              ^ (evdev / sysfs)
+-------------------------------------------------------------+
| Capa 1: Kernel & Controladores (/dev/input/event*)          |
+-------------------------------------------------------------+
```

---

## 2. Secuencia Atómica de Diagnóstico

### Paso 1: Validar Capa Kernel (evdev)
Comprobar si el hardware emite eventos crudos al kernel:
```bash
sudo evtest /dev/input/event0   # Probar teclado
sudo evtest /dev/input/event4   # Probar touch (o el evento correspondiente según /proc/bus/input/devices)
```
- **Esperado:** Al tocar la pantalla o pulsar teclas, la terminal muestra ráfagas `SYN_REPORT`, `ABS_MT_POSITION_X`, `KEY_A`, etc.
- **Si falla:** Problema de cableado USB/I2C o módulo de kernel no cargado. Detener diagnóstico aquí.

### Paso 2: Validar Capa de Asiento y libinput fuera del Compositor
Comprobar que `seatd` y `libinput` procesan los eventos de dispositivo:
```bash
systemctl status seatd
sudo libinput debug-events
```
- **Esperado:** Al interactuar físicamente, `libinput debug-events` imprime eventos `POINTER_MOTION`, `TOUCH_DOWN`, `KEYBOARD_KEY` con el nombre exacto del dispositivo.
- **Si falla:** Permisos del usuario sobre el grupo `input`/`video` o fallo en el daemon `seatd`.

### Paso 3: Validar Inicialización del Backend en wlroots (`labwc`)
Comprobar si el compositor incluye el backend `libinput` en tiempo de ejecución:
```bash
# Verificar variables de entorno del proceso labwc en ejecución
PID=$(pgrep -f "/usr/bin/labwc" | head -n 1)
tr '\0' '\n' < /proc/$PID/environ | grep "^WLR_BACKENDS="
```
- **Esperado:** `WLR_BACKENDS=drm,libinput` (O la variable ausente para detección por defecto).
- **Si aparece `WLR_BACKENDS=drm` únicamente:** El compositor NUNCA abrirá `/dev/input/event*`. Corregir en `~/.config/labwc/environment` y `/etc/systemd/system/magi-kiosk.service`.

Para inspección detallada con debug:
```bash
WLR_LOG_LEVEL=debug labwc 2>&1 | tee /tmp/labwc_debug.log &
grep -E "libinput|backend" /tmp/labwc_debug.log
```

### Paso 4: Validar Interacción en Cliente Mínimo Wayland
Antes de lanzar Chromium (que tiene capas de aislamiento, sandboxing y flags complejas), probar un cliente simple de Wayland:
```bash
WAYLAND_DISPLAY=wayland-0 weston-terminal
```
- **Esperado:** El teclado escribe en la terminal y los clics/toques son recibidos.

### Paso 5: Validar Flags de Chromium y Mapeo Táctil
Una vez que el compositor y Wayland responden:
- Verificar flags en `magi-kiosk.service`:
  `--ozone-platform=wayland --enable-features=UseOzonePlatform,WaylandWindowDecorations,TouchTextSelection --touch-events=enabled`
- Verificar mapeo en `~/.config/labwc/rc.xml`:
  ```xml
  <touch>
    <mapToOutput>HDMI-A-1</mapToOutput>
  </touch>
  ```

---

## 3. Checklist Rápido de Recuperación
Ejecutar el script automatizado:
```bash
bash scripts/verify-input-stack.sh
```
Si todos los checks están en `[OK]`, la interacción física está garantizada.
