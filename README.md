# MASTER REPOSITORY: HIL-RTOS DIGITAL TWIN & REAL-TIME HYPERVISOR

## 1. Visión General del Proyecto
Este repositorio alberga la infraestructura de software, gobernanza agéntica, herramientas de introspección profunda y el **Gemelo Digital** para el banco de pruebas **Hardware-in-the-Loop (HIL)** basado en **Raspberry Pi 5 (BCM2712 - 4x Cortex-A76)** ejecutando un kernel determinista de tiempo real (**Debian GNU/Linux 13 Trixie / SMP PREEMPT_RT**).

El propósito principal es dotar al sistema de capacidades de simulación y emulación en tiempo real duro (latencias < 50 μs), garantizando determinismo estricto, tolerancia a fallas, auditoría continua de ejecución y sincronización bidireccional de artefactos con la estación anfitriona Lenovo ThinkPad L480.

---

## 2. Arquitectura del Repositorio Local

```
E:\alons\Documents\Raspberry HIL\
├── RULES.md                      # Axiomas inmutables de seguridad, confinamiento y RTOS
├── ROLES.md                      # Jerarquía multi-agente y matriz de privilegios
├── COMMAND_EXECUTION_AUDIT.md    # Bitácora técnica estructurada de auditoría
├── PI_STATE_OF_ART.md            # Manifiesto empírico exhaustivo del estado del target
├── README.md                     # Documentación arquitectónica maestra
├── docs/                         # Guías técnicas, topología y diseño de bajo nivel
│   ├── ARCHITECTURE.md           # Diseño del hipervisor y separación de dominios
│   ├── DETERMINISTIC_RTOS.md     # Principios de latencia determinista y PREEMPT_RT
│   └── NETWORK_TOPOLOGY.md       # Diagrama y protocolos de enlace Ethernet / Wi-Fi
└── Digital_Twin_Workspace/       # Espejo físico-lógico del sistema remoto (Gemelo Digital)
    ├── boot_firmware/            # config.txt, cmdline.txt, device tree overlays
    ├── etc/                      # Configuraciones críticas (NetworkManager, systemd, sysctl)
    ├── home_alonso/              # Scripts de usuario, herramientas y bash history
    └── hardware_maps/            # Mapas de pines GPIO, periféricos I2C/SPI/UART y PCI-e
```

---

## 3. Principios de Diseño para Sistemas Operativos Resilientes y Escalables
1. **Determinismo Temporal Estricto:** Utilización del parche `PREEMPT_RT` en el kernel Linux para convertir todas las secciones críticas e interrupciones en hilos planificables (`ksoftirqd`, hilos `irq/`), minimizando la latencia de despacho.
2. **Aislamiento de Cargas (Domain Separation):** Partición de núcleos de CPU entre el dominio de gestión/telemetría (Core 0) y los dominios de ejecución HIL de tiempo real duro (Cores 1-3).
3. **No Interferencia en Silicio:** Preservación inmutable de afinidades de interrupciones, estados C y P de la CPU, y gobernadores de reloj fijos para eliminar el jitter introducido por ahorro de energía.
4. **Resiliencia en Comunicaciones:** Enlace dual redundante (Ethernet físico directo de baja latencia + Wi-Fi 5 GHz para telemetría y acceso administrativo).
5. **Gobernanza Agéntica Autónoma:** Protocolos O-I-P-E-V-R con auto-aprobación y auditoría no repudiable en `COMMAND_EXECUTION_AUDIT.md`.
