# Arquitectura y Estructura Canónica del Repositorio (`v1.0-stable`)

Esta estructura define la organización canónica y única fuente de verdad para el proyecto HIL-RTOS Digital Twin tras la consolidación de la versión estable `v1.0-stable`.

```
.
├── .env.example                     # Plantilla pública segura de variables de entorno
├── .env.local                       # Credenciales locales SSH y endpoints (IGNORADO por Git)
├── .gitignore                       # Filtros de exclusión estricta de Git
├── AGENTS.md                        # Directivas operacionales y de gobernanza para agentes AI
├── AGENTS_ROLES_AND_CONTEXT.md      # Asignación de roles y contexto arquitectónico
├── ARCHITECTURE_DIAGRAM.md          # Diagramas de arquitectura del sistema
├── COMMAND_EXECUTION_AUDIT.md       # Auditoría de comandos y ejecuciones forenses
├── GIT_GOVERNANCE_AUDIT.md          # Auditoría de gobernanza Git y trazabilidad
├── PI_STATE_OF_ART.md               # Estado del arte de la Raspberry Pi 5 y Linux RT
├── README.md                        # Resumen ejecutivo del proyecto
├── README_MASTER.md                 # Manual maestro técnico de la estación HIL
├── RESILIENCE_GAP_ANALYSIS.md       # Análisis de brechas de resiliencia y tolerancia a fallos
├── ROLES.md                         # Matriz de roles del equipo de ingeniería
├── RULES.md                         # Reglas maestras de desarrollo y operación
├── STATE_OF_THE_ART.md              # Estado del arte del sistema
│
├── config/                          # CONFIGURACIONES CANÓNICAS DEL SISTEMA
│   ├── boot/                        # Configuración de firmware y kernel boot
│   │   ├── cmdline.txt              # Parámetros del kernel Linux RT (aislamiento CPU, video DRM)
│   │   └── config.txt               # Overlays de dispositivo (vc4-kms-v3d, SPI, I2C, I2S)
│   ├── labwc/                       # Configuración canónica del compositor Wayland
│   │   ├── environment              # Variables de entorno (WLR_BACKENDS=drm,libinput, etc.)
│   │   └── rc.xml                   # Reglas de ventanas, foco y mapeo táctil a HDMI-A-1
│   ├── network/                     # Red y broker MQTT
│   │   ├── LUANA 5G.nmconnection    # Perfil NetworkManager
│   │   └── mosquitto.conf           # Configuración del broker MQTT
│   ├── security/                    # Límites de tiempo real y sysctl
│   │   ├── 10-coredump-debian.conf
│   │   ├── 98-rpi.conf
│   │   ├── 99-realtime.conf         # Prioridades rtprio y memlock para usuario alonso
│   │   ├── fstab
│   │   ├── limits.conf
│   │   ├── modules
│   │   ├── os-release
│   │   └── sysctl.conf
│   └── systemd/                     # Unidades systemd canónicas de producción
│       ├── autologin.conf           # Override getty para autologin
│       ├── hil-ipc.service          # Demonio IPC de memoria compartida
│       ├── hil-rt.service           # Bucle determinista de control en Core 2/3
│       ├── magi-kiosk.service       # Kiosko Wayland + Chromium HMI en Core 1
│       ├── magi-ttyd.service        # Terminal web interactiva
│       ├── magi-ui.service          # Servidor web Flask HMI
│       └── seatd.service            # Demonio de gestión de asiento (seat0)
│
├── docs/                            # DOCUMENTACIÓN Y GOBERNANZA TÉCNICA
│   ├── backlog.md                   # Backlog de deuda técnica, prevención y roadmap
│   ├── cleanup-log.md               # Registro exhaustivo de clasificación de archivos
│   ├── repo-structure.md            # Este documento: topología canónica del repositorio
│   ├── runbook-input-debugging.md   # Runbook de diagnóstico del stack de entrada Wayland
│   ├── ARCHITECTURE.md              # Documentación de arquitectura de alto nivel
│   ├── DETERMINISTIC_RTOS.md        # Especificación del determinismo en Linux PREEMPT_RT
│   ├── NETWORK_TOPOLOGY.md          # Topología de red e interfaces
│   ├── canonical-state/             # Estado congelado verificado en hardware real
│   │   ├── full-file-inventory.txt  # Inventario completo de archivos del repo
│   │   ├── hardware-verification-status.txt # Output literal de verificación en Pi 5
│   │   ├── labwc.environment.known-good     # Copia fiel de ~/.config/labwc/environment
│   │   ├── labwc.rc.xml.known-good          # Copia fiel de ~/.config/labwc/rc.xml
│   │   ├── magi-kiosk.service.known-good    # Copia fiel de /etc/systemd/system/magi-kiosk.service
│   │   └── seatd.service.known-good         # Copia fiel de /lib/systemd/system/seatd.service
│   └── postmortem/                  # Post-mortems de incidentes
│       └── 2026-08-29-touch-input-outage.md # Post-mortem del incidente de WLR_BACKENDS
│
├── scripts/                         # SCRIPTS OPERACIONALES ACTIVOS
│   ├── verify-input-stack.sh        # Verificación automatizada del stack de entrada en hardware
│   └── automation/                  # Herramientas de despliegue y sincronización continua
│       ├── deploy_magi_remote.py    # Despliegue remoto y reinicio de la HMI MAGI
│       ├── env_loader.py            # Cargador seguro de entorno (.env.local)
│       ├── generate_state_of_art.py # Generador de reportes de estado del arte
│       ├── install_streamer.py      # Instalador de herramientas de streaming
│       ├── install_tools.py         # Instalador de utilidades en la Raspberry Pi
│       ├── introspect.py            # Introspección profunda de hardware y kernel
│       ├── restart_kiosk.py         # Reinicio seguro del kiosko HMI
│       └── sync_digital_twin.py     # Sincronización bidireccional del gemelo digital
│
├── src/                             # CÓDIGO FUENTE DE APLICACIÓN ACTIVA
│   ├── hmi_ui/                      # Servidor e interfaz web MAGI (Flask + WebSockets)
│   │   ├── magi_server.py           # Backend Flask y enrutador de telemetría
│   │   ├── static/                  # Recursos estáticos (CSS, JS)
│   │   │   ├── css/magi.css
│   │   │   └── js/                  # Scripts de frontend (magi.js, keyboard.js, network.js)
│   │   └── templates/
│   │       └── index.html           # Plantilla principal del panel MAGI
│   ├── ipc_bridge/                  # Puente de comunicación inter-proceso
│   │   └── ipc_daemon.cpp           # Demonio C++ de sincronización y SHM
│   └── rt_core/                     # Núcleo determinista en tiempo real
│       ├── LockFreeQueue.hpp        # Colas atómicas sin bloqueo (SPSC)
│       ├── SharedState.hpp          # Estructuras de memoria compartida
│       └── rt_motor.cpp             # Modelo dinámico de motor y lazo de control
│
├── Digital_Twin_Workspace/          # SNAPSHOT MIRROR DEL SISTEMA OPERATIVO REMOTO
├── telemetry/                       # CAPTURAS DE PANTALLA Y REGISTROS FORENSES
│
└── _archive/                        # ARCHIVO HISTÓRICO CON PRESERVACIÓN DE ESTRUCTURA
    └── pre-cleanup-20260829/        # Scripts de diagnóstico ad-hoc y fases intermedias archivadas
        └── scripts/automation/
```
