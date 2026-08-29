# Resumen de Auditoría, Saneamiento y Consolidación de Repositorio (2026-08-29)

- **Fecha:** 2026-08-29
- **Tag de Seguridad Previo:** `pre-cleanup-20260829`
- **Tag de Versión Estable:** `v1.0-stable`
- **Rama Canónica:** `main` (Merge `--no-ff` completado)

---

## 1. Índice de Documentos y Artefactos Canónicos

1. **Post-Mortem del Incidente de Entrada:**
   - [`docs/postmortem/2026-08-29-touch-input-outage.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/postmortem/2026-08-29-touch-input-outage.md)
2. **Estado Canónico Congelado (Hardware Real):**
   - Directorio: [`docs/canonical-state/`](file:///e:/alons/Documents/Raspberry%20HIL/docs/canonical-state/)
3. **Registro de Clasificación y Auditoría Archivo por Archivo:**
   - [`docs/cleanup-log.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/cleanup-log.md)
4. **Estructura Canónica del Repositorio:**
   - [`docs/repo-structure.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/repo-structure.md)
5. **Backlog de Deuda Técnica y Hoja de Ruta:**
   - [`docs/backlog.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/backlog.md)
6. **Runbook de Diagnóstico del Subsistema de Entrada:**
   - [`docs/runbook-input-debugging.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/runbook-input-debugging.md)
7. **Script de Verificación Automatizado:**
   - [`scripts/verify-input-stack.sh`](file:///e:/alons/Documents/Raspberry%20HIL/scripts/verify-input-stack.sh)
8. **Directivas para Agentes Antigravity:**
   - [`AGENTS.md`](file:///e:/alons/Documents/Raspberry%20HIL/AGENTS.md)

---

## 2. Adenda de Subsanación — 2026-08-29 (Auditoría de la Consolidación)

Esta sección documenta la subsanación atómica de los 7 puntos observados en la auditoría de la consolidación:

### Fallo 1: Merge canónico a `main` y reubicación de `v1.0-stable`
- Rama activa: `main`
- Commit merge: `d88dd3f merge: consolidate v1.0-stable cleanup into main`
- Output literal:
```text
$ git branch --show-current
main

$ git log -n 1 --oneline
d88dd3f merge: consolidate v1.0-stable cleanup into main

$ git tag -l
pre-cleanup-20260829
v1.0-stable
v6.1.0
v8.0.0
```

### Fallo 2: Corrección y resolución dinámica por nombre en `scripts/verify-input-stack.sh`
- Captura de verdad de terreno en `/proc/bus/input/devices`:
  - `event0`: `QDtech MPI7003` (Pantalla táctil)
  - `event1`: `HOLTEK USB Keyboard` (Teclado)
  - `event7`: `vc4-hdmi-0 HDMI Jack` (Audio ALSA, excluido)
- Output literal de la corrida del script corregido en hardware real:
```text
========================================================================
>>> [1/5] VERIFICANDO SERVICIOS SYSTEMD ACTIVOS...
========================================================================
  [OK] seatd: ACTIVO
  [OK] magi-ui: ACTIVO
  [OK] magi-kiosk: ACTIVO

========================================================================
>>> [2/5] RESOLVIENDO DISPOSITIVOS DE ENTRADA REALES (KERNEL / PROC)...
========================================================================
  [OK] Pantalla Táctil Detectada:
       Nombre: "QDtech MPI7003"
       Nodo:   /dev/input/event0
       Estado: Dispositivo presente en filesystem (/dev/input/event0)
  [OK] Teclado Físico Detectado:
       Nombre: "HOLTEK USB Keyboard"
       Nodo:   /dev/input/event1
       Estado: Dispositivo presente en filesystem (/dev/input/event1)
  [INFO] Dispositivos de audio/CEC excluidos de input humano:
         - "pwr_button"
         - "vc4-hdmi-0"
         - "vc4-hdmi-0 HDMI Jack"

========================================================================
>>> [3/5] VERIFICANDO VARIABLES DE ENTORNO EN MAGI-KIOSK...
========================================================================
  [OK] PID de labwc: 1090
  [STATUS] WLR_BACKENDS=drm,libinput
  [OK] libinput presente en WLR_BACKENDS de labwc

========================================================================
>>> [4/5] VERIFICANDO GESTION DE ASIENTO (SEATD / LIBSEAT)...
========================================================================
  [OK] Socket /run/seatd.sock activo

========================================================================
>>> [5/5] VERIFICANDO LOGS DE COMPOSITOR Y CLIENTE HMI...
========================================================================
  [OK] Cero errores criticos de libinput en journal recent

========================================================================
>>> VERIFICACION COMPLETADA CON EXITO: STACK DE ENTRADA CERTIFICADO
========================================================================
```

### Fallo 3 & Fallo 4: Confirmación física del operador y persistencia post-reinicio limpio

#### Respuesta literal del operador en hardware físico:
> *"Sí, inicia con magi"*  
> *"sí, cambia a Autonomous agent // baltasar . 2"*  
> *"sí, abre el modal de networkl"*  
> *"sí, el mouse y teclado usb funcionan"*

#### Persistencia tras booteo limpio (`sudo reboot` sin intervención manual):
- Durante el primer reboot se identificó que `magi-kiosk.service` estaba en estado `disabled`; se ejecutó `systemctl enable magi-kiosk.service` y se lanzó un segundo reinicio en frío.
- Output literal tras el arranque:
```text
>>> systemctl is-active seatd magi-ui magi-kiosk
active
active
active

>>> Uptime:
 17:05:47 up 0 min,  2 users,  load average: 2.08, 0.50, 0.17
```


### Fallo 5: Limpieza de `override.conf` en `seatd.service.d`
- Output literal de verificación:
```text
=== Check seatd.service.d BEFORE ===
ls: cannot access '/etc/systemd/system/seatd.service.d/': No such file or directory

=== Check override.conf BEFORE ===
cat: /etc/systemd/system/seatd.service.d/override.conf: No such file or directory

=== Check seatd.service.d AFTER ===
ls: cannot access '/etc/systemd/system/seatd.service.d/': No such file or directory
```

### Fallo 6: Muestra verificable de 3 filas del `docs/cleanup-log.md`
- Total de líneas en `docs/cleanup-log.md`: 192 líneas (175 archivos).
- Muestras auditadas con grep de referencias:
  1. **CANÓNICO:** `magi_server.py`
     - Fila: `| Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/magi_server.py | 2026-08-29 11:55 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en Digital_Twin_Workspace/ |`
     - Coincidencias en repo: `config/systemd/magi-ui.service`, `scripts/automation/deploy_magi_remote.py`, `scripts/automation/restart_kiosk.py`, `docs/repo-structure.md`, `README_MASTER.md`.
  2. **DUPLICADO OBSOLETO:** `deploy_labwc_migration.py`
     - Fila: `| scripts/automation/deploy_labwc_migration.py | 2026-08-29 15:59 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a _archive/pre-cleanup-20260829/scripts/automation/ |`
     - Coincidencias en repo activo: 0 referencias.
  3. **CÓDIGO ZOMBIE:** `env_loader.cpython-314.pyc`
     - Fila: `| scripts/automation/__pycache__/env_loader.cpython-314.pyc | 2026-08-29 12:17 | Ninguna (0 refs) | **CÓDIGO ZOMBIE** | Eliminar (Artefacto compilado transitorio) |`
     - Coincidencias en repo activo: 0 referencias.

### Fallo 7: Comprobación de funcionalidad HTTP/HMI tras reorganización
- Output literal tras `systemctl restart magi-ui magi-kiosk`:
```text
>>> systemctl is-active magi-ui magi-kiosk
active
active

>>> curl -I http://127.0.0.1:8080
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.5
Date: Sat, 29 Aug 2026 23:05:55 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 23550
Connection: close
```
- Journal de `magi-ui`:
```text
127.0.0.1 - - [29/Aug/2026 17:04:12] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [29/Aug/2026 17:04:12] "GET /static/js/keyboard.js HTTP/1.1" 304 -
127.0.0.1 - - [29/Aug/2026 17:04:12] "GET /static/js/network.js HTTP/1.1" 304 -
127.0.0.1 - - [29/Aug/2026 17:04:12] "GET /static/css/magi.css HTTP/1.1" 304 -
127.0.0.1 - - [29/Aug/2026 17:04:13] "GET /api/status HTTP/1.1" 200 -
```
