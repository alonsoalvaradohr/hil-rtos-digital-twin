# Post-Mortem: Interrupción del Subsistema de Entrada Táctil y Teclado en Kiosko HMI

- **Fecha del Incidente:** 2026-08-29
- **Afectación:** Subsistema de Interacción Física / Interfaz de Kiosko HMI Wayland
- **Estado:** Resuelto / Mitigado / Verificado en Hardware Real
- **Severidad:** P1 (Bloqueo total de interacción física en Workstation HIL)

---

## 1. Síntoma Observado
Durante la inicialización del kiosko HMI sobre la pantalla HDMI física (1024x600), la pantalla táctil (`WaveShare Waveshare Touchscreen`) y el teclado USB físico no generaban respuesta interactiva alguna dentro de la interfaz gráfica del navegador Chromium/compositor, a pesar de que el kernel (`/dev/input/event*`) y las herramientas de diagnóstico a nivel de consola (`evtest`) registraban eventos de entrada perfectamente continuos y calibrados.

---

## 2. Impacto
La estación de trabajo HIL (Hardware-in-the-Loop) quedó inoperable para control manual directo desde la consola física durante la sesión de depuración (~6 horas de degradación interactiva). El sistema dependía exclusivamente de inyecciones sintéticas CDP/WebSocket o comandos SSH remotos para operar la interfaz.

---

## 3. Causa Raíz Real y Verificada
La variable de entorno:
```bash
WLR_BACKENDS=drm
```
definida tanto en `~/.config/labwc/environment` como en la unidad systemd `/etc/systemd/system/magi-kiosk.service`, forzaba a la biblioteca wlroots a inicializar **únicamente** el backend de vídeo Direct Rendering Manager (`drm`), omitiendo por completo el backend de entrada `libinput`.

Como consecuencia directa:
1. El compositor Wayland (`labwc`) jamás abría los descriptores de archivo en `/dev/input/event*`.
2. `labwc` no creaba ni exponía capacidades de touch (`wl_touch`), puntero (`wl_pointer`) ni teclado (`wl_keyboard`) en su objeto global `wl_seat`.
3. Aunque `libinput debug-events` (ejecutado independientemente en consola) demostraba que el kernel, udev y `seatd` funcionaban correctamente, `labwc` era ciego a los eventos de hardware.

---

## 4. Corrección Aplicada
Se reconfiguró la variable canónica en la unidad de systemd y en el entorno del compositor para incluir explícitamente ambos backends:
```ini
Environment=WLR_BACKENDS=drm,libinput
```

Archivos actualizados:
- `/etc/systemd/system/magi-kiosk.service`
- `~/.config/labwc/environment`
- `config/systemd/magi-kiosk.service`
- `config/labwc/environment`

---

## 5. Cómo se Diagnosticó (Secuencia Real)
El diagnóstico definitivo se obtuvo aplicando aislamiento estricto de abajo hacia arriba en el stack:

1. **Capa Kernel / Dispositivos:** Se ejecutó `evtest` directamente sobre `/dev/input/event0` (teclado) y `/dev/input/event4` (pantalla táctil), confirmando la emisión de paquetes `EV_ABS`, `EV_SYN` y `EV_KEY`.
2. **Capa libinput & Gestión de Asiento:** Se ejecutó `libinput debug-events` con `seatd` activo fuera del compositor, confirmando que libinput y udev reconocían los dispositivos sin restricción de permisos.
3. **Capa Compositor (wlroots Debug):** Se inició `labwc` con `WLR_LOG_LEVEL=debug` redirigido a archivo log. La inspección con:
   ```bash
   grep -c libinput labwc_debug.log
   ```
   arrojó **0 coincidencias**, revelando que wlroots ni siquiera intentaba inicializar el subsistema libinput.
4. **Verificación de la Corrección:** Al cambiar `WLR_BACKENDS=drm,libinput` y relanzar con `WLR_LOG_LEVEL=debug`, el log mostró **10 coincidencias** detallando la inicialización del backend libinput y la vinculación de cada dispositivo de entrada.
5. **Verificación Física en Hardware:** Se validó la respuesta táctil y de teclado primero en un cliente Wayland mínimo (`weston-terminal`) antes de relanzar Chromium, aislando cualquier comportamiento del navegador.

---

## 6. Falsos Caminos Explorados y Descartados

| Hipótesis Explorada | Acción Tomada | Por qué se Descartó |
| :--- | :--- | :--- |
| **`seatd` VT-bound** | Se aplicó override `SEATD_VTBOUND=0` y modificación del servicio `seatd`. | `seatd` ya concedía acceso a los dispositivos sin problemas; wlroots nunca le solicitaba abrir `/dev/input/` debido a `WLR_BACKENDS=drm`. |
| **D-Bus Session Bus ausente** | Se investigó si la falta de `DBUS_SESSION_BUS_ADDRESS` bloqueaba eventos en Chromium. | En Wayland, Chromium recibe eventos de entrada directamente mediante el protocolo `wl_seat` de Wayland, no mediante D-Bus. |
| **Chromium Sandbox** | Se agregaron flags `--no-sandbox` y `--disable-setuid-sandbox`. | El fallo ocurría en el compositor antes de despachar eventos a cualquier cliente Wayland. |
| **Reglas udev de Seat / uaccess** | Se creó `/etc/udev/rules.d/99-magi-touch-input.rules` con tags `seat0` y `uaccess`. | Los permisos de grupo `input`/`video` y la pertenencia del usuario eran suficientes; el bloqueo era la configuración interna de wlroots. |
| **Limitaciones de Cage Kiosk** | Se migró el compositor de `cage` a `labwc`. | `labwc` heredó la misma variable `WLR_BACKENDS=drm` mal configurada, reproduciendo el síntoma idéntico. |
| **Conflicto de TTY / Getty Hijack** | Se configuró `StandardInput=null` y deshabilitó `user-host`. | Necesario para evitar robo de caracteres en TTY, pero no era la causa de la ausencia de eventos Wayland. |
| **Perfiles corruptos / Singletons Chromium** | Se añadieron limpiezas `rm -rf /tmp/chromium_magi_profile/Singleton*`. | Corregía bloqueos de arranque de Chromium, pero no tenía relación con la falta de eventos táctiles. |

---

## 7. Por Qué se Tardó en Diagnosticar
La causa principal del retraso en el diagnóstico fue la **falta de aislamiento incremental por capas**. Se modificaron simultáneamente parámetros de Chromium, systemd, udev, seatd y el compositor sin validar de forma aislada e independiente cada interfaz del stack (Kernel → libinput → Compositor/wlroots → Cliente Wayland/Chromium).

---

## 8. Acciones Preventivas
1. **Script de Verificación Automatizado (`scripts/verify-input-stack.sh`):** Inspección obligatoria de logs de wlroots tras cada despliegue para validar `libinput` antes de dar por bueno un servicio.
2. **Runbook de Diagnóstico Atómico (`docs/runbook-input-debugging.md`):** Procedimiento estandarizado de abajo hacia arriba para incidentes de entrada.
3. **Consolidación de Single Source of Truth:** Centralizar unidades systemd y configuraciones de compositor en `/config/systemd` y `/config/labwc`, eliminando duplicados obsoletos.
