# ARQUITECTURA DEL SISTEMA HIL-RTOS (ARCHITECTURE.md)

## 1. Visión Arquitectónica
El sistema HIL (Hardware-in-the-Loop) implementa una arquitectura desacoplada y determinista orientada a la emulación de componentes físicos, sensores y actuadores con restricciones temporales duras.

```
+-------------------------------------------------------------------------+
|                  HOST WORKSTATION (Lenovo ThinkPad L480)                |
|  - Windows 11 Host OS                                                   |
|  - Digital Twin Workspace (`[HIL_WORKSPACE_REDACTED] HIL`)          |
|  - Orquestador de Pruebas & AGENT-CORE                                  |
+------------------------------------+------------------------------------+
                                     |  Dual Physical Link
                +--------------------+--------------------+
                |                                         |
         Ethernet Directo                          Wi-Fi 5 GHz
       (fe80::4b3c:e19:bb19:445a)                 ("LUANA 5G")
                |                                         |
+---------------v-----------------------------------------v---------------+
|                   TARGET REMOTO (Raspberry Pi 5 Model B)                |
|  - SoC: Broadcom BCM2712 (4x ARM Cortex-A76 @ 2.4 GHz)                 |
|  - Kernel: Linux 6.18.34+rpt-rpi-v8-rt (SMP PREEMPT_RT)                |
|  - Debian 13 (Trixie) 64-bit                                            |
|                                                                         |
|  +---------------------------+  +------------------------------------+  |
|  | DOMINIO DE TIEMPO REAL    |  | DOMINIO DE GESTIÓN Y TELEMETRÍA    |  |
|  | - HIL Plant Emulators     |  | - SSH Daemon (Port 22)             |  |
|  | - Protocolos Bus (CAN/SPI)|  | - NetworkManager (nmcli)           |  |
|  | - SCHED_FIFO Prio 99      |  | - Systemd / Journald               |  |
|  | - Núcleos Aislados RT     |  | - Core 0 (Housekeeping)            |  |
|  +---------------------------+  +------------------------------------+  |
+-------------------------------------------------------------------------+
```

## 2. Separación de Dominios
1. **Dominio de Housekeeping (Core 0):** Procesa interrupciones generales de red, comandos SSH, registros en disco y tareas de mantenimiento del sistema operativo.
2. **Dominio de Tiempo Real HIL (Cores 1..3):** Dedicado exclusivamente a los bucles de cálculo HIL deterministas, sin interferencia de temporizadores de software ni balanceo dinámico de carga.
