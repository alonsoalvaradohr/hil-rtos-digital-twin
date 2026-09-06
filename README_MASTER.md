# MASTER ARCHITECTURAL REPOSITORY: HIL-RTOS INDUSTRIAL HYPERVISOR & DIGITAL TWIN

**Target Silicio:** Raspberry Pi 5 (Broadcom BCM2712 - 4x ARM Cortex-A76 @ 2.4 GHz, 16GB LPDDR4X-4267)  
**Estación Anfitriona:** Lenovo ThinkPad L480 (Windows 11 / PowerShell / AntiGravity CLI)  
**Arquitectura del Kernel:** Debian GNU/Linux 13 (Trixie) con Parche Industrial `SMP PREEMPT_RT` (Kernel 6.18.34+rpt-rpi-v8-rt aarch64)  
**Estándar de Seguridad y Confinamiento:** MISRA C++ / ISO-26262 ASIL-D Ready / Determinismo Temporal Duro (Latencias < 15 μs)  

---

## 🌐 CENTRO DE MANDO GLOBAL (QUICK ACCESS)

> **ACCESO OPERACIONAL ZERO-TRUST Y PASSTHROUGH SENSORIAL TOTAL**  
> Enlaces directos de alta disponibilidad para supervisión, telemetría táctica, consola remota y control sensorial bidireccional desde cualquier red global sin apertura de puertos.

| Subsistema | Enlace Directo | Descripción Operacional |
| :--- | :--- | :--- |
| **MAGI HMI Nativo** | [Acceder a MAGI HMI](https://disk-ventures-market-investing.trycloudflare.com/) | Interfaz base táctica Evangelion pura de 1024x600. Ideal para supervisión de telemetría y control táctil. |
| **Inmersión Sensorial Total** | [Acceder a Espejo Sensorial](https://disk-ventures-market-investing.trycloudflare.com/mirror) | HUD de inmersión completa: streaming de video Wayland, control de puntero/teclado, micrófono remoto (PCM 16 kHz hacia ALSA loopback) y altavoz WebRTC. |
| **Terminal Zero-Trust** | [Acceder a Terminal Web](https://disk-ventures-market-investing.trycloudflare.com/terminal/) | Consola interactiva `ttyd` / Bash integrada directamente en el navegador, protegida por túnel TLS 1.3. |
| **noVNC Puro** | [Acceder a noVNC Kiosk](https://disk-ventures-market-investing.trycloudflare.com/vnc/vnc_lite.html) | Espejo de pantalla completa de bajo nivel sobre el compositor Wayland (`wayvnc` + `websockify`). Diagnóstico del escritorio en bruto. |
| **Enlace SSH Global** | `ssh -p 6 alonso@a.pinggy.io` | Túnel TCP inverso para administración remota por terminal SSH (autenticación mediante clave Ed25519). |

---

## 1. Visión Holística del Proyecto (Zero to Hero)

El proyecto **HIL-RTOS Digital Twin & Real-Time Hypervisor** es una plataforma de ingeniería avanzada para la simulación, validación en tiempo real y emulación en bucle cerrado (*Hardware-in-the-Loop*) de sistemas ciberfísicos críticos. El banco de pruebas está diseñado para albergar modelos de plantas de potencia, control vectorial de servomotores, actuadores aeroespaciales e instrumentación automotriz en un entorno con determinismo temporal absoluto.

Históricamente, los sistemas de prueba HIL han requerido costosos equipos propietarios como dSPACE, Speedgoat u OPAL-RT. Este desarrollo demuestra la viabilidad de lograr un determinismo temporal estricto (< 15 microsegundos de jitter máximo) sobre computación embebida de bajo costo utilizando el procesador Broadcom BCM2712 de la Raspberry Pi 5, optimizado mediante partición de silicio y un parche de kernel `PREEMPT_RT`.

El ecosistema integra cinco subsistemas sinérgicos:
1. **Gemelo Digital Espejo (`Digital_Twin_Workspace/` y `telemetry/`):** Instantánea física y lógica del árbol de configuración, bootloader, device tree overlays y mapas de interrupciones del hardware target.
2. **Motor Determinista de Tiempo Real (`src/rt_core/`):** Módulo C++ que implementa el solucionador numérico de la planta (1 kHz) anclado exclusivamente al Core 3 bajo la política de planificación `SCHED_FIFO` con prioridad 99 y prefaulting de memoria (`mlockall`).
3. **Puente IPC Lock-Free Asíncrono (`src/ipc_bridge/`):** Demonio desacoplado (`ipc_daemon`) que traslada comandos y telemetría entre la memoria compartida POSIX (`/dev/shm/hil_shm`) y el broker MQTT Mosquitto en los Cores de gestión.
4. **HMI Táctil MAGI (`src/hmi_ui/`):** Interfaz gráfica táctil de 1024x600 con estética táctica Evangelion ejecutándose sobre Wayland/Cage y Chromium Kiosk anclados al Core 1.
5. **Gobernanza y Trazabilidad Multi-Agente:** Protocolo de consenso cognitivo no interactivo (O-I-P-E-V-R) con auditoría estricta en `COMMAND_EXECUTION_AUDIT.md` y `GIT_GOVERNANCE_AUDIT.md`.

---

## 2. Topología de Silicio y Aislamiento de Dominios

El procesador Broadcom BCM2712 cuenta con 4 núcleos ARM Cortex-A76. Para erradicar la contención de recursos, la pérdida de caché y el jitter introducido por las interrupciones del sistema operativo, el procesador se divide en tres dominios ortogonales:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      BROADCOM BCM2712 (4x ARM CORTEX-A76 @ 2.4 GHz)             │
├────────────────────────────────┬─────────────────┬──────────────────────────────┤
│ CORE 0: Gestión & Housekeeping │ CORE 1: Gráficos│ CORES 2 & 3: TIEMPO REAL DURO│
│ • Linux Kernel OS Tasks        │ • Wayland (Cage)│ • isolcpus=2,3               │
│ • Servidor SSH (sshd)          │ • Chromium Kiosk│ • nohz_full=2,3              │
│ • Mosquitto MQTT Broker        │ • MAGI Flask UI │ • rcu_nocbs=2,3              │
│ • NetworkManager (WiFi/Eth)    │ • ttyd Terminal │ • SCHED_FIFO Prioridad 99    │
│ • Demonio IPC Bridge           │ • Touch & OSK   │ • Lazo HIL 1 kHz (Anti-Drift)│
└────────────────────────────────┴─────────────────┴──────────────────────────────┘
```

- **Core 0 (Dominio de Housekeeping y Comunicaciones):** Gestiona la pila TCP/IP, el servidor SSH, las transferencias SFTP, el gestor de redes NetworkManager y el broker MQTT Mosquitto.
- **Core 1 (Dominio Gráfico y Terminal Táctil):** Aloja el servidor web backend Flask (`magi_server.py`), el emulador web de terminal `ttyd` (puerto 7681) y el compositor Wayland en modo kiosko (`cage`), eliminando cualquier interferencia visual sobre los cores RT.
- **Cores 2 y 3 (Dominio de Silicio Aislado / Hard Real-Time):** Aislados en el arranque mediante los parámetros `isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3` en `/boot/firmware/cmdline.txt`. El kernel de Linux no asigna tareas generales a estos núcleos ni genera interrupciones periódicas de temporizador (*tickless mode*). El proceso `rt_motor` se fija al Core 3 con afinidad de CPU estricta.

---

## 3. Jerarquía Canónica del Repositorio

```
E:lons\Documents\Raspberry HIL├── src/                               # Código fuente modular del sistema
│   ├── rt_core/                       # Núcleo de Tiempo Real Duro (Cores 2 y 3)
│   │   ├── LockFreeQueue.hpp          # Cola circular SPSC Lock-Free alineada a 64 bytes
│   │   ├── SharedState.hpp            # Estructuras de Memoria Compartida e Idempotencia
│   │   └── rt_motor.cpp               # Emulador de planta determinista a 1 kHz
│   ├── ipc_bridge/                    # Demonio de Intercomunicación Asíncrona (Core 0)
│   │   └── ipc_daemon.cpp             # Traductor bidireccional MQTT <-> SHM
│   └── hmi_ui/                        # Servidor e Interfaz Táctil MAGI (Core 1)
│       ├── magi_server.py             # Backend Flask & API NetworkManager/Bluetooth
│       ├── static/                    # Hojas de estilo CSS y lógica JS modular
│       │   ├── css/magi.css           # Tema oscuro táctico Evangelion (1024x600)
│       │   └── js/                    # magi.js (control), network.js (WiFi), keyboard.js (OSK)
│       └── templates/index.html       # Plantilla maestra de la HMI con 3 pods hexagonales
├── config/                            # Archivos de configuración persistente del sistema
│   ├── systemd/                       # hil-rt.service, hil-ipc.service, magi-*.service
│   ├── boot/                          # config.txt y cmdline.txt con aislamiento de CPU
│   ├── network/                       # Perfiles de red Wi-Fi y configuración Mosquitto
│   └── security/                      # limits.d/99-realtime.conf y sysctl.conf
├── scripts/                           # Herramientas de automatización y telemetría
│   └── automation/                    # introspect.py, sync_digital_twin.py, etc.
├── telemetry/                         # Mapas de silicio empíricos e introspección
│   └── hardware_maps/                 # Topología de CPU, memoria, PCIe, USB, GPIO, IRQs
├── docs/                              # Documentación técnica de arquitectura y diseño
├── README_MASTER.md                   # Este documento maestro (Zero to Hero)
├── ARCHITECTURE_DIAGRAM.md            # Diagramas visuales Mermaid asíncronos
├── STATE_OF_THE_ART.md                # Manifiesto consolidado de logros de ingeniería
├── DEVELOPMENT_BACKLOG.md             # Hoja de ruta para futuras fases de hardware
└── AGENTS_ROLES_AND_CONTEXT.md        # Definición formal de roles de IA y gobernanza
```

---

## 4. Guía de Compilación, Despliegue y Verificación

### 4.1. Compilación de Binarios C++ en Raspberry Pi 5
```bash
# Compilar el motor de tiempo real (Core 3, SCHED_FIFO 99)
g++ -O3 -Wall -std=c++17 src/rt_core/rt_motor.cpp -o src/rt_core/rt_motor -lrt

# Compilar el puente IPC (Core 0, MQTT <-> SHM)
g++ -O3 -Wall -std=c++17 src/ipc_bridge/ipc_daemon.cpp -o src/ipc_bridge/ipc_daemon -lmosquitto -lrt
```

### 4.2. Activación y Orquestación Systemd
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mosquitto.service
sudo systemctl enable --now hil-ipc.service
sudo systemctl enable --now hil-rt.service
sudo systemctl enable --now magi-ui.service
sudo systemctl enable --now magi-ttyd.service
sudo systemctl enable --now magi-kiosk.service
```

### 4.3. Verificación de Funcionamiento y Telemetría
```bash
# Comprobar estado de los servicios
systemctl status hil-rt.service hil-ipc.service magi-kiosk.service

# Monitorear telemetría viva a 1 kHz desde terminal
mosquitto_sub -t "hil/telemetry" -v

# Enviar comando de velocidad al emulador de motor
mosquitto_pub -t "hil/command" -m '{"action_id":1,"speed":150.0,"flags":1}'

# Ejecutar parada de emergencia (E-STOP)
mosquitto_pub -t "hil/emergency_stop" -m '{"action_id":999}'
```

---

## 5. Operación Rápida para Técnicos de Laboratorio

```bash
# Actualizar a la versión estable de producción:
git checkout main && git pull origin main

# Actualizar a la versión de desarrollo / pruebas:
git checkout develop && git pull origin develop

# Re-sincronizar el Gemelo Digital desde la Raspberry Pi:
python scripts/automation/introspect.py && python scripts/automation/sync_digital_twin.py
```
