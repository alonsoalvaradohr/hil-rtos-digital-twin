# ARQUITECTURA DEL SISTEMA Y DIAGRAMAS DE FLUJO: HIL-RTOS HYPERVISOR

**Proyecto:** Hipervisor Industrial Hardware-in-the-Loop Determinista  
**Target:** Raspberry Pi 5 (Broadcom BCM2712 - 4x Cortex-A76)  
**Host:** Lenovo ThinkPad L480 (Windows 11 / AntiGravity CLI)  

---

## 1. Diagrama de Separación de Dominios de Silicio

El siguiente diagrama ilustra la partición física de núcleos de CPU en el SoC BCM2712, las afinidades de procesamiento y el aislamiento de las interrupciones del kernel:

```mermaid
graph TB
    subgraph SOC["BROADCOM BCM2712 (4x ARM CORTEX-A76 @ 2.4 GHz)"]
        subgraph DOMAIN_MGMT["DOMINIO DE GESTIÓN (Core 0)"]
            OS["Linux Kernel 6.18 PREEMPT_RT"]
            NET["Pila TCP/IP & WiFi (wlan0) / GbE (eth0)"]
            SSH["Servidor OpenSSH (Puerto 22)"]
            MQTT["Mosquitto MQTT Broker (Puerto 1883)"]
            IPC["Demonio IPC Bridge (ipc_daemon)"]
        end

        subgraph DOMAIN_UI["DOMINIO GRÁFICO & TERMINAL (Core 1)"]
            WAYLAND["Compositor Wayland (Cage / Labwc)"]
            CHROMIUM["Chromium Kiosk (Ozone-Wayland)"]
            FLASK["MAGI Server Flask (Puerto 8080)"]
            TTYD["Terminal Web ttyd (Puerto 7681)"]
        end

        subgraph DOMAIN_RT["DOMINIO TIEMPO REAL DURO (Cores 2 y 3 - Aislados)"]
            ISOL["isolcpus=2,3 | nohz_full=2,3 | rcu_nocbs=2,3"]
            ENGINE["Motor Determinista HIL (rt_motor)<br/>• SCHED_FIFO Prioridad 99<br/>• mlockall (Sin Page Faults)<br/>• Lazo 1 kHz clock_nanosleep"]
            PHYSICS["Emulador de Planta / Servomotor<br/>dw/dt = (K*u - w) / Tau"]
        end
    end

    subgraph MEMORY["MEMORIA RAM COMPARTIDA (/dev/shm/hil_shm)"]
        HEADER["Cabecera de Idempotencia & Heartbeats"]
        QUEUE_CMD["Cola SPSC Comandos (web_to_hardware)<br/>Lock-Free • 64B Cache-Aligned • 1024 Slots"]
        QUEUE_TLM["Cola SPSC Telemetría (hardware_to_web)<br/>Lock-Free • 64B Cache-Aligned • 1024 Slots"]
    end

    IPC -->|Push Comandos| QUEUE_CMD
    QUEUE_CMD -->|Pop Comandos| ENGINE
    ENGINE -->|Push Telemetría| QUEUE_TLM
    QUEUE_TLM -->|Pop Telemetría| IPC
    IPC -->|Publica hil/telemetry| MQTT
    FLASK -->|Comandos HTTP/JSON| MQTT
    CHROMIUM -->|Visualización 1024x600| FLASK
```

---

## 2. Diagrama de Estructura de Memoria Compartida y Caché ARM64

Para erradicar la invalidación de líneas de caché (*False Sharing*) entre el Core 0 (productor/consumidor de red) y el Core 3 (consumidor/productor RT), cada estructura atómica y buffer está estrictamente alineado a 64 bytes (`alignas(64)`):

```mermaid
classDiagram
    class HILSharedMemoryHeader {
        +uint64_t magic = 0x48494C5F53484D32
        +uint32_t version = 0x00020000
        +atomic~uint32_t~ is_initialized
        +atomic~uint64_t~ rt_heartbeat_tick [64B]
        +atomic~uint64_t~ ipc_heartbeat_tick [64B]
        +atomic~uint64_t~ dropped_commands_count [64B]
        +atomic~uint64_t~ dropped_telemetry_count [64B]
        +atomic~uint32_t~ emergency_stop_active [64B]
    }

    class LockFreeQueue_Command {
        -HILCommand buffer[1024] [alignas 64]
        -atomic~size_t~ head [alignas 64]
        -atomic~size_t~ tail [alignas 64]
        +push(HILCommand) bool [Release]
        +pop(HILCommand&) bool [Acquire]
    }

    class LockFreeQueue_Telemetry {
        -HILTelemetry buffer[1024] [alignas 64]
        -atomic~size_t~ head [alignas 64]
        -atomic~size_t~ tail [alignas 64]
        +push(HILTelemetry) bool [Release]
        +pop(HILTelemetry&) bool [Acquire]
    }

    class HILSharedMemory {
        +HILSharedMemoryHeader header
        +LockFreeQueue_Command web_to_hardware
        +LockFreeQueue_Telemetry hardware_to_web
    }

    HILSharedMemory *-- HILSharedMemoryHeader
    HILSharedMemory *-- LockFreeQueue_Command
    HILSharedMemory *-- LockFreeQueue_Telemetry
```

---

## 3. Flujo de Mensajería Bidireccional Asíncrona (MQTT <-> SHM <-> RT Core)

```mermaid
sequenceDiagram
    autonumber
    participant UI as HMI Táctil MAGI (Chromium/JS)
    participant Flask as Backend Flask (magi_server.py)
    participant MQTT as Mosquitto MQTT Broker
    participant IPC as Demonio IPC (ipc_daemon)
    participant SHM as Memoria Compartida (/dev/shm)
    participant RT as Motor RT (rt_motor / Core 3)

    Note over UI,Flask: Dominio Gráfico (Core 1)
    UI->>Flask: POST /api/hil/command {speed: 150.0}
    Flask->>MQTT: mosquitto_pub "hil/command"
    Note over MQTT,IPC: Dominio Housekeeping (Core 0)
    MQTT->>IPC: on_message() callback
    IPC->>SHM: web_to_hardware.push(cmd) [Memory Order Release]
    
    Note over RT: Dominio Tiempo Real Duro (Core 3 - 1 kHz)
    loop Ciclo Determinista (Ts = 1 ms)
        RT->>RT: clock_nanosleep(TIMER_ABSTIME)
        RT->>SHM: web_to_hardware.pop(cmd) [Memory Order Acquire]
        RT->>RT: dw/dt = (K*u - w) / Tau
        RT->>SHM: hardware_to_web.push(telem) [Memory Order Release]
        RT->>SHM: rt_heartbeat_tick++
    end

    IPC->>SHM: hardware_to_web.pop(telem) [Memory Order Acquire]
    IPC->>MQTT: mosquitto_pub "hil/telemetry" {seq, speed, lat_ns}
    Flask->>UI: SSE / API Polling Telemetría Viva
    UI->>UI: Actualiza tacómetro y gráficos de jitter
```

---

## 4. Pila de Software del Modo Kiosko Wayland en Core 1

```mermaid
graph TD
    subgraph HW["PANTALLA TÁCTIL 7 PULGADAS (1024x600)"]
        DSI["Panel DSI / HDMI (DRM/KMS /dev/dri/card0)"]
        TOUCH["Digitalizador I2C Goodix / FT5406 (/dev/input/event*)"]
    end

    subgraph SYSTEMD["ORQUESTACIÓN SYSTEMD (Core 1)"]
        SEATD["seatd.service (Gestión de sesiones sin display manager)"]
        KIOSK["magi-kiosk.service (Compositor Cage Wayland)"]
        UI_SRV["magi-ui.service (Servidor Flask 8080)"]
        TTYD_SRV["magi-ttyd.service (Terminal Web 7681)"]
    end

    subgraph RUNTIME["ENTORNO DE EJECUCIÓN WAYLAND"]
        CAGE["Cage 0.2.0 (Compositor Wayland Monotarea)"]
        CHROME["Chromium 134+ (Bandera: --ozone-platform=wayland --kiosk)"]
        MAGI_APP["MAGI Frontend (HTML5 / CSS3 / Vanilla JS / OSK Virtual)"]
    end

    SEATD --> KIOSK
    KIOSK --> CAGE
    CAGE --> CHROME
    CHROME --> MAGI_APP
    MAGI_APP --> UI_SRV
    MAGI_APP --> TTYD_SRV
    DSI --- CAGE
    TOUCH --- CAGE
```
