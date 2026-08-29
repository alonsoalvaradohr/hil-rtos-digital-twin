# Registro de Auditoría y Clasificación de Repositorio (Cleanup Log)

- **Fecha de Auditoría:** 2026-08-29
- **Tag de Seguridad Previo:** `pre-cleanup-20260829` (permite recuperación de cualquier archivo previo al saneamiento)
- **Total de Archivos Auditados:** 175

## Criterios de Clasificación
- **CANÓNICO:** Código activo de producción, configuraciones sincronizadas con el hardware verificado, documentación maestra y scripts de operación recurrente.
- **DUPLICADO OBSOLETO:** Versiones intermedias de scripts de despliegue (`deploy_phase*.py`, `apply_*.py`) superseded por la configuración canónica final.
- **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ:** Herramientas forenses y pruebas puntuales (`forensic_*.py`, `test_*.py`) creadas para aislar el incidente.
- **CÓDIGO ZOMBIE:** Archivos sin referencia alguna en imports, servicios o scripts operativos (`__pycache__`).
- **DESCONOCIDO:** Archivos con rol no determinable con evidencia directa (ninguno sin resolver).

## Tabla Completa de Inventario y Clasificación

| Archivo | Última modificación | Referenciado por (systemd/import/script) | Clasificación | Acción |
| :--- | :--- | :--- | :--- | :--- |
| `.env.example` | 2026-08-29 12:13 | Cargador de entorno (.env_loader / Git) | **CANÓNICO** | Conservar en raíz (Entorno/Git) |
| `.env.local` | 2026-08-29 13:40 | Cargador de entorno (.env_loader / Git) | **CANÓNICO** | Conservar en raíz (Entorno/Git) |
| `.gitignore` | 2026-08-29 12:13 | Cargador de entorno (.env_loader / Git) | **CANÓNICO** | Conservar en raíz (Entorno/Git) |
| `AGENTS_ROLES_AND_CONTEXT.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `ARCHITECTURE_DIAGRAM.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `COMMAND_EXECUTION_AUDIT.md` | 2026-08-29 13:44 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `DEVELOPMENT_BACKLOG.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `Digital_Twin_Workspace/boot_firmware/cmdline.txt` | 2026-08-29 12:28 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/boot_firmware/config.txt` | 2026-08-29 12:58 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/NetworkManager/system-connections/LUANA 5G.nmconnection` | 2026-08-28 07:25 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/fstab` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/modules` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/mosquitto/mosquitto.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/os-release` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/security/limits.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/security/limits.d/10-coredump-debian.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/security/limits.d/99-realtime.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/sysctl.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/sysctl.d/98-rpi.conf` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/getty@tty1.service.d/autologin.conf` | 2026-08-25 19:35 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/hil-ipc.service` | 2026-08-25 16:55 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/hil-rt.service` | 2026-08-25 16:55 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/magi-kiosk.service` | 2026-08-29 16:21 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/magi-ttyd.service` | 2026-08-25 19:10 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/systemd/system/magi-ui.service` | 2026-08-25 19:03 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/etc/udev/rules.d/99-magi-touch-input.rules` | 2026-08-29 14:57 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/block_devices.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/cpu_isolation_state.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/cpu_topology.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/gpio_bus_nodes.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/interrupts_map.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/loaded_modules.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/memory_map.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/network_interfaces.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/pcie_topology.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/realtime_threads.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/hardware_maps/usb_topology.txt` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home/alonso/.config/labwc/rc.xml` | 2026-08-29 16:24 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.bash_history` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.bash_profile` | 2026-08-25 19:36 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.bashrc` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.config/autostart/hmi-kiosk.desktop` | 2026-08-25 19:11 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.config/labwc/autostart` | 2026-08-25 19:35 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.config/labwc/environment` | 2026-08-25 19:35 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/.profile` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/01_system_tuning/boot_config/cmdline_original.bak` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/01_system_tuning/boot_config/config_original.bak` | 2026-08-25 16:43 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/02_ipc_core/LockFreeQueue.hpp` | 2026-08-25 16:54 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/02_ipc_core/SharedState.hpp` | 2026-08-25 16:54 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/02_ipc_core/ipc_daemon.cpp` | 2026-08-25 16:54 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/02_ipc_core/rt_motor.cpp` | 2026-08-25 16:55 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/magi_server.py` | 2026-08-29 11:55 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/static/css/magi.css` | 2026-08-29 14:24 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/static/js/keyboard.js` | 2026-08-25 19:02 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/static/js/magi.js` | 2026-08-29 14:07 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/static/js/network.js` | 2026-08-29 14:07 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/home_alonso/hil_workstation/05_hmi_display/templates/index.html` | 2026-08-29 14:24 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `Digital_Twin_Workspace/raw_introspection.json` | 2026-08-25 16:42 | Snapshot de introspección / sync_digital_twin | **CANÓNICO** | Conservar en `Digital_Twin_Workspace/` (Snapshot de introspección) |
| `GIT_GOVERNANCE_AUDIT.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `PI_STATE_OF_ART.md` | 2026-08-25 16:43 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `README.md` | 2026-08-28 07:25 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `README_MASTER.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `RESILIENCE_GAP_ANALYSIS.md` | 2026-08-25 16:51 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `ROLES.md` | 2026-08-25 16:40 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `RULES.md` | 2026-08-25 16:40 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `STATE_OF_THE_ART.md` | 2026-08-28 07:59 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `config/boot/cmdline.txt` | 2026-08-29 12:28 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/boot/cmdline_original.bak` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/boot/config.txt` | 2026-08-29 12:58 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/boot/config_original.bak` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/network/LUANA 5G.nmconnection` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/network/mosquitto.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/10-coredump-debian.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/98-rpi.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/99-realtime.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/fstab` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/limits.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/modules` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/os-release` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/security/sysctl.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/autologin.conf` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/hil-ipc.service` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/hil-rt.service` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/magi-kiosk.service` | 2026-08-29 16:21 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/magi-ttyd.service` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `config/systemd/magi-ui.service` | 2026-08-28 07:59 | Unidad/Configuración de sistema HIL | **CANÓNICO** | Conservar en `/config` (Configuración canónica) |
| `docs/ARCHITECTURE.md` | 2026-08-25 16:40 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/DETERMINISTIC_RTOS.md` | 2026-08-25 16:40 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/NETWORK_TOPOLOGY.md` | 2026-08-25 16:40 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/canonical-state/hardware-verification-status.txt` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/canonical-state/labwc.environment.known-good` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/canonical-state/labwc.rc.xml.known-good` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/canonical-state/magi-kiosk.service.known-good` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/canonical-state/seatd.service.known-good` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `docs/postmortem/2026-08-29-touch-input-outage.md` | 2026-08-29 16:57 | Documentación de arquitectura/auditoría | **CANÓNICO** | Conservar en `/docs` o raíz (Gobernanza/Docs) |
| `scripts/automation/__pycache__/env_loader.cpython-314.pyc` | 2026-08-29 12:17 | Ninguna (0 refs) | **CÓDIGO ZOMBIE** | Eliminar (Artefacto compilado transitorio) |
| `scripts/automation/apply_seatd_vtbound_fix.py` | 2026-08-29 15:34 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/apply_udev_fix.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/capture_real_hdmi.py` | 2026-08-29 12:19 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/check_udev.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/clean_and_verify_seat.py` | 2026-08-29 15:22 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_and_test_live.py` | 2026-08-29 14:25 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_labwc_migration.py` | 2026-08-29 15:59 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_magi_remote.py` | 2026-08-28 07:59 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/deploy_phase10_fix.py` | 2026-08-29 13:40 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_phase10_real_sync.py` | 2026-08-29 13:41 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_phase11_canonical.py` | 2026-08-29 15:34 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_phase15_nosandbox.py` | 2026-08-29 16:10 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_phase16_consolidation.py` | 2026-08-29 16:21 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/deploy_touch_mapping.py` | 2026-08-29 16:25 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/env_loader.py` | 2026-08-29 12:13 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/execute_6_step_sequence.py` | 2026-08-29 14:32 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/execute_phase14_remediation.py` | 2026-08-29 16:08 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/extract_forensic_phase13.py` | 2026-08-29 16:01 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/forensic_investigation.py` | 2026-08-29 14:25 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/forensic_phase11_diag.py` | 2026-08-29 15:34 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/forensic_phase13_audit.py` | 2026-08-29 16:01 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/generate_state_of_art.py` | 2026-08-28 07:59 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/inspect_live_fds.py` | 2026-08-29 15:48 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/install_streamer.py` | 2026-08-29 14:25 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/install_tools.py` | 2026-08-29 14:09 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/introspect.py` | 2026-08-28 07:59 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/investigate_input_pipeline.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/prepare_local_console_launch.py` | 2026-08-29 16:24 | Ninguna (0 refs) | **DUPLICADO OBSOLETO** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/pure_ws_cdp.py` | 2026-08-29 14:33 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/restart_kiosk.py` | 2026-08-29 12:13 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/step1_observe.py` | 2026-08-29 14:09 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/step2_investigate.py` | 2026-08-29 14:09 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/sync_digital_twin.py` | 2026-08-28 07:59 | Ninguna (0 refs) | **CANÓNICO** | Conservar en `/scripts` (Script operacional) |
| `scripts/automation/test_builtin_seat.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_hardware_events.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_kiosk_stability.py` | 2026-08-29 15:48 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_labwc_hardware_event.py` | 2026-08-29 16:01 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_labwc_kiosk.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_manual_input.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_tty_ownership.py` | 2026-08-29 14:57 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `scripts/automation/test_wtype.py` | 2026-08-29 16:01 | Ninguna (0 refs) | **SCRIPT DE DIAGNÓSTICO DE UNA SOLA VEZ** | Mover a `_archive/pre-cleanup-20260829/scripts/automation/` |
| `src/hmi_ui/magi_server.py` | 2026-08-29 11:55 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/hmi_ui/static/css/magi.css` | 2026-08-29 15:34 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/hmi_ui/static/js/keyboard.js` | 2026-08-28 07:59 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/hmi_ui/static/js/magi.js` | 2026-08-29 15:34 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/hmi_ui/static/js/network.js` | 2026-08-29 15:34 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/hmi_ui/templates/index.html` | 2026-08-29 14:25 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/ipc_bridge/ipc_daemon.cpp` | 2026-08-28 07:59 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/rt_core/LockFreeQueue.hpp` | 2026-08-28 07:59 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/rt_core/SharedState.hpp` | 2026-08-28 07:59 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `src/rt_core/rt_motor.cpp` | 2026-08-28 07:59 | Módulo de aplicación activa (Flask/RT-Core/IPC) | **CANÓNICO** | Conservar en `/src` (Código activo) |
| `telemetry/01_magi_main.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/02_click_network.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/03_network_panel.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/04_back_to_magi.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/05_click_balthasar.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/06_balthasar_panel.png` | 2026-08-29 14:33 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/forensic_phase13_report.txt` | 2026-08-29 15:58 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/block_devices.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/cpu_isolation_state.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/cpu_topology.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/gpio_bus_nodes.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/interrupts_map.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/loaded_modules.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/memory_map.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/network_interfaces.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/pcie_topology.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/realtime_threads.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/hardware_maps/usb_topology.txt` | 2026-08-28 07:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/magi_screen_labwc_live.png` | 2026-08-29 15:53 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/magi_screen_live.png` | 2026-08-29 15:35 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/magi_screen_nosandbox.png` | 2026-08-29 16:10 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/magi_screen_phase16.png` | 2026-08-29 16:18 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/magi_screen_remediated.png` | 2026-08-29 16:08 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/real_screen.png` | 2026-08-29 13:39 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/screen_after_hw_event.png` | 2026-08-29 14:52 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/screen_labwc.png` | 2026-08-29 14:55 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/screen_labwc_hw_touch.png` | 2026-08-29 15:58 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
| `telemetry/screenshot_min_00.png` | 2026-08-29 12:59 | Evidencia forense / telemetría | **CANÓNICO** | Conservar en `telemetry/` (Evidencia forense) |
