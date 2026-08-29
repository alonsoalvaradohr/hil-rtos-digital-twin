# Resumen de Auditoría, Saneamiento y Consolidación de Repositorio (2026-08-29)

- **Fecha:** 2026-08-29
- **Tag de Seguridad Previo:** `pre-cleanup-20260829`
- **Tag de Versión Estable:** `v1.0-stable`
- **Rama:** `feature/phase9.5-ultimate-forensic-fix` (Consolidada para merge canónico)

---

## 1. Índice de Documentos y Artefactos Producidos

1. **Post-Mortem del Incidente de Entrada:**
   - [`docs/postmortem/2026-08-29-touch-input-outage.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/postmortem/2026-08-29-touch-input-outage.md)
   - Documenta síntoma, impacto, causa raíz (`WLR_BACKENDS=drm` sin `libinput`), corrección aplicada, secuencia de diagnóstico y falsas hipótesis descartadas.

2. **Estado Canónico Congelado (Hardware Real):**
   - Directorio: [`docs/canonical-state/`](file:///e:/alons/Documents/Raspberry%20HIL/docs/canonical-state/)
   - Archivos:
     - `labwc.environment.known-good`
     - `labwc.rc.xml.known-good`
     - `magi-kiosk.service.known-good`
     - `seatd.service.known-good`
     - `hardware-verification-status.txt`
     - `full-file-inventory.txt`

3. **Registro de Clasificación y Auditoría Archivo por Archivo:**
   - [`docs/cleanup-log.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/cleanup-log.md)
   - 175 archivos clasificados bajo las categorías canónicas (`CANÓNICO`, `DUPLICADO OBSOLETO`, `SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ`, `CÓDIGO ZOMBIE`).

4. **Estructura Canónica del Repositorio:**
   - [`docs/repo-structure.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/repo-structure.md)
   - Define la distribución oficial de `/src`, `/config`, `/docs`, `/scripts` y `/_archive`.

5. **Backlog de Deuda Técnica y Hoja de Ruta:**
   - [`docs/backlog.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/backlog.md)
   - Registra deudas técnicas detectadas, medidas preventivas y épicas del roadmap HIL-RTOS.

6. **Runbook de Diagnóstico del Subsistema de Entrada:**
   - [`docs/runbook-input-debugging.md`](file:///e:/alons/Documents/Raspberry%20HIL/docs/runbook-input-debugging.md)
   - Secuencia atómica de 5 pasos por capas de abajo hacia arriba.

7. **Script de Verificación Automatizado:**
   - [`scripts/verify-input-stack.sh`](file:///e:/alons/Documents/Raspberry%20HIL/scripts/verify-input-stack.sh)
   - Script POSIX ejecutable en el hardware target para certificar el stack de entrada y wlroots.

8. **Directivas para Agentes Antigravity:**
   - [`AGENTS.md`](file:///e:/alons/Documents/Raspberry%20HIL/AGENTS.md)
   - Normas estrictas de verificación obligatoria con output literal, aislamiento de cambios y mantenimiento mensual.

---

## 2. Acciones Ejecutadas

1. **Extracción de Estado Canónico:** Se conectó vía SSH/SFTP a la Raspberry Pi 5 (`AlonsoRTOS`, 192.168.100.30) y se extrajeron las configuraciones activas y demostradas en hardware real hacia `docs/canonical-state/`.
2. **Generación de Tag de Seguridad:** Se fijó `git tag pre-cleanup-20260829` antes de mover archivos.
3. **Auditoría Exhaustiva:** Se inspeccionaron los 175 archivos del árbol del repositorio, determinando referencias cruzadas con `ripgrep`.
4. **Purga Segura a Archivo Histórico:** Se trasladaron 33 scripts de despliegues intermedios y herramientas forenses ad-hoc a `_archive/pre-cleanup-20260829/scripts/automation/` preservando rutas relativas. Se eliminó la caché compilada transitoria `__pycache__`.
5. **Sincronización de Configuraciones:** Se actualizaron `config/systemd/magi-kiosk.service`, `config/systemd/seatd.service`, `config/labwc/environment` y `config/labwc/rc.xml` con los parámetros canónicos.
6. **Ejecución y Certificación en Hardware:** Se ejecutó `scripts/verify-input-stack.sh` directamente en la Raspberry Pi 5.

---

## 3. Evidencias y Outputs Literales de Verificación

### Output Literal 1: Ejecución de `scripts/verify-input-stack.sh` en la Raspberry Pi 5
```text
========================================================================
>>> [1/5] VERIFICANDO SERVICIOS SYSTEMD ACTIVOS...
========================================================================
  [OK] seatd: ACTIVO
  [OK] magi-ui: ACTIVO
  [OK] magi-kiosk: ACTIVO

========================================================================
>>> [2/5] VERIFICANDO DISPOSITIVOS DE ENTRADA EN KERNEL...
========================================================================
  [OK] Dispositivo /dev/input/event0 presente (Teclado/Mouse)
  [OK] Dispositivo de entrada táctil: /dev/input/event7

========================================================================
>>> [3/5] VERIFICANDO VARIABLES DE ENTORNO EN MAGI-KIOSK...
========================================================================
  [OK] PID de labwc: 20512
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
>>> VERIFICACION COMPLETADA CON EXITO: STACK DE ENTRADA OPERATIVO
========================================================================
```

### Output Literal 2: Estado de Servicios `systemctl status seatd magi-ui magi-kiosk`
```text
● seatd.service - Seat management daemon
     Loaded: loaded (/lib/systemd/system/seatd.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-08-29 16:52:27 CST; 7min ago
   Main PID: 20494 (seatd)
      Tasks: 1 (limit: 8874)
     Memory: 228.0K (peak: 340.0K)
        CPU: 13ms
     CGroup: /system.slice/seatd.service
             └─20494 /usr/bin/seatd -g video

● magi-ui.service - MAGI System UI Server (Core 0 - Flask Backend)
     Loaded: loaded (/etc/systemd/system/magi-ui.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-08-29 16:52:27 CST; 7min ago
   Main PID: 20496 (python3)
      Tasks: 5 (limit: 8874)
     Memory: 29.5M (peak: 30.6M)
        CPU: 1.157s
     CGroup: /system.slice/magi-ui.service
             └─20496 /usr/bin/python3 /home/alonso/hil_workstation/05_hmi_display/magi_server.py

● magi-kiosk.service - MAGI Wayland Kiosk Compositor (Core 1 - Interactive Labwc)
     Loaded: loaded (/etc/systemd/system/magi-kiosk.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-08-29 16:52:27 CST; 7min ago
    Process: 20509 ExecStartPre=/bin/rm -rf /tmp/chromium_magi_profile/Singleton* (code=exited, status=0/SUCCESS)
   Main PID: 20512 (labwc)
      Tasks: 44 (limit: 8874)
     Memory: 174.5M (peak: 205.8M)
        CPU: 22.311s
     CGroup: /system.slice/magi-kiosk.service
             ├─20512 /usr/bin/labwc -s "/usr/bin/chromium-browser --no-sandbox --disable-setuid-sandbox --kiosk ..."
             ├─20527 /usr/lib/chromium/chromium --no-sandbox --disable-setuid-sandbox --kiosk ...
             ├─20531 /usr/lib/chromium/chromium-sandbox /usr/lib/chromium/chromium --type=zygote ...
```

---

## 4. Estado de Git y Tags Canónicos
- Tag de seguridad: `pre-cleanup-20260829`
- Tag de versión consolidada: `v1.0-stable`
