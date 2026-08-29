# Backlog de Ingeniería, Deuda Técnica y Hoja de Ruta (v1.0-stable)

- **Proyecto:** Hipervisor Industrial Hardware-in-the-Loop (HIL-RTOS Digital Twin)
- **Versión Consolidada:** `v1.0-stable`
- **Última Actualización:** 2026-08-29

---

## 1. Deuda Técnica Identificada Durante el Incidente

### DT-01: Fragmentación de Fuentes de Verdad en Unidades systemd
- **Problema:** Existían copias divergentes de `magi-kiosk.service` en `/config/systemd/`, `/Digital_Twin_Workspace/etc/systemd/system/` y scripts ad-hoc en `scripts/automation/`.
- **Resolución / Estado:** Consolidado en `v1.0-stable`. La única fuente de verdad canónica del repositorio es `/config/systemd/magi-kiosk.service`, sincronizada directamente con `/etc/systemd/system/magi-kiosk.service` en el hardware.
- **Acción Pendiente:** Integrar en el script de deploy (`scripts/automation/deploy_magi_remote.py`) la sincronización bidireccional automática con hash check.

### DT-02: Ausencia de Pruebas de Humo Automatizadas Post-Reinicio
- **Problema:** Las verificaciones se realizaban reiniciando servicios individuales (`systemctl restart`), omitiendo validar el estado tras un reinicio frío (`reboot`).
- **Resolución / Estado:** Se creó `scripts/verify-input-stack.sh`.
- **Acción Pendiente:** Programar ejecución automática de `verify-input-stack.sh` vía systemd timer post-boot para telemetría continua de salud del quiosco.

### DT-03: Falta de Validación Estricta de Variables de Entorno de wlroots
- **Problema:** La omisión de `libinput` en `WLR_BACKENDS` pasó desapercibida hasta la prueba de interacción física manual.
- **Resolución / Estado:** Mitigado en `scripts/verify-input-stack.sh` (Paso 3) y documentado en `docs/runbook-input-debugging.md`.

---

## 2. Prevención Operativa y Gobernanza

- [x] **PREV-01:** Script de verificación de subsistema de entrada (`scripts/verify-input-stack.sh`).
- [x] **PREV-02:** Runbook estandarizado de diagnóstico por capas (`docs/runbook-input-debugging.md`).
- [x] **PREV-03:** Directiva estricta en `AGENTS.md` exigiendo evidencia literal por comando antes de declarar fixes como operativos.

---

## 3. Próximos Pasos Funcionales Pendientes (Roadmap HIL-RTOS)

### ÉPICA 1: Inyección de Señales GPIO Rápidas y PWM por DMA (Fase 9)
- [ ] **TASK-09-01:** Implementar driver de acceso directo a registros GPIO utilizando `/dev/gpiomem4` (Southbridge RP1) para conmutación de pines en sub-microsegundos (< 100 ns).
- [ ] **TASK-09-02:** Diseñar generador de pulsos PWM determinista mediante DMA cíclico para emulación de señales de encoder incremental (canales A, B, Z) hasta 500 kHz.
- [ ] **TASK-09-03:** Añadir protección de sobrecorriente por software y verificación de límites de tensión en entradas GPIO.

### ÉPICA 2: Integración de Buses SPI y Solucionadores Numéricos en Silicio (Fase 10)
- [ ] **TASK-10-01:** Configurar driver `spidev` con buffers DMA en modo full-duplex a 50 MHz para emulación de ADC/DAC SPI de 16 bits.
- [ ] **TASK-10-02:** Implementar integrador Runge-Kutta de 4to orden (RK4) en C++ optimizado con instrucciones ARM Neon / SIMD para modelos de plantas no lineales de alta dimensión.
- [ ] **TASK-10-03:** Integrar soporte para exportación directa de modelos Simulink / Modelica en código C++ compatible con `LockFreeQueue.hpp`.

### ÉPICA 3: Gateway de Comunicaciones Industriales y CAN-FD (Fase 11)
- [ ] **TASK-11-01:** Integrar controlador CAN-FD vía transceptor SPI (MCP2518FD / TCAN4550) con soporte SocketCAN nativo en Linux RT.
- [ ] **TASK-11-02:** Implementar pila de protocolos de telemetría automotriz (UDS / ISO 14229 y XCP on CAN) en el Core 0.
- [ ] **TASK-11-03:** Añadir soporte para transporte industrial TSN (Time-Sensitive Networking / IEEE 802.1Qbv) sobre la interfaz Ethernet `eth0`.

### ÉPICA 4: Cualificación Aeroespacial y Certificación de Seguridad (Fase 12)
- [ ] **TASK-12-01:** Ejecutar análisis estático de código conforme a las reglas MISRA C++:2023 y AUTOSAR Adaptive Platform mediante herramientas certificadas (Cppcheck, Clang-Tidy, SonarQube).
- [ ] **TASK-12-02:** Generar matriz de trazabilidad bidireccional de requisitos a pruebas (DO-178C Nivel A / ISO 26262 ASIL-D), cubriendo el 100% de Modified Condition/Decision Coverage (MC/DC).
- [ ] **TASK-12-03:** Implementar *Watchdog* por hardware en el Southbridge RP1 con reinicio seguro, apagado determinista de actuadores y transición a estado a prueba de fallos (*Fail-Safe State*).
