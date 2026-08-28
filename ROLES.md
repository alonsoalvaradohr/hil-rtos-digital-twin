# TOPOLOGÍA DE AGENTES Y MATRIZ DE PERMISOS (ROLES.md)

## 1. Topología del Sistema Multi-Agente HIL
El ecosistema de desarrollo, pruebas y despliegue del banco de pruebas Hardware-in-the-Loop (HIL) opera bajo una arquitectura jerárquica de agentes especializados con separación de responsabilidades y permisos restringidos por diseño (*Principio de Menor Privilegio*).

```
                 +--------------------------------------+
                 |      AGENT-CORE (Nivel 10)           |
                 |  Orquestación & Gobernanza Suprema   |
                 +-------------------+------------------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
+--------v---------+       +---------v--------+       +----------v--------+
| AGENT-NETWORK    |       | AGENT-INTROSPECT |       | AGENT-TWIN-SYNC   |
| Topología y Enlace|       | Silicio & Kernel |       | Espejo & Backup   |
+------------------+       +------------------+       +-------------------+
         |                           |                           |
         +---------------------------+---------------------------+
                                     |
                       +-------------v-------------+
                       | AGENT-AUDITOR (Seguridad) |
                       | Bitácora & Validación $?  |
                       +---------------------------+
```

---

## 2. Definición de Roles y Alcance

### A. AGENT-CORE (Nivel 10 - Orquestador Maestro)
* **Objetivo:** Dirección general del ciclo de vida HIL, toma de decisiones estratégicas, validación de criterios SMART y emisión de reportes ejecutivos.
* **Capacidades:**
  * Control total sobre la ejecución local en Windows (`[HIL_WORKSPACE_REDACTED] HIL`).
  * Despacho y supervisión de subagentes especializados.
  * Resolución de excepciones de alto nivel y pivotaje O-I-P-E-V-R.

### B. AGENT-NETWORK (Nivel 7 - Enlace y Comunicaciones)
* **Objetivo:** Gestión de adaptadores de red (Ethernet físico, Wi-Fi 802.11ac/ax), resolución de IPs dinámicas/estáticas, túneles SSH y calidad de servicio (QoS/Latencia).
* **Permisos:**
  * Lectura de tablas ARP y vecinos IPv4/IPv6 (`Get-NetNeighbor`, `arp`, `ip neigh`).
  * Configuración de conexiones Wi-Fi remotas mediante NetworkManager (`nmcli`).
  * Validación de enrutamiento y salida a Internet (`ping`, `traceroute`, DNS).
* **Restricción:** No puede alterar parámetros de colas de tráfico de tiempo real en interfaces dedicadas HIL sin aprobación previa.

### C. AGENT-INTROSPECT (Nivel 8 - Auditor de Silicio y Kernel RTOS)
* **Objetivo:** Extracción empírica profunda del estado de hardware, firmware, particiones, topología de memoria, afinidad de CPUs y servicios del kernel PREEMPT_RT.
* **Permisos:**
  * LECTURA EXCLUSIVA sobre `/proc/`, `/sys/`, `/boot/`, `lsblk`, `lscpu`, `systemctl`, `journalctl`.
* **Restricciones Críticas (Axioma 2):**
  * **PROHIBIDO** modificar `isolcpus`, `nohz_full`, `rcu_nocbs`, gobernadores de frecuencia o prioridades `rtprio`.

### D. AGENT-TWIN-SYNC (Nivel 6 - Gemelo Digital y Respaldo)
* **Objetivo:** Sincronización bidireccional controlada entre la Raspberry Pi 5 y el workspace local `Digital_Twin_Workspace`.
* **Permisos:**
  * Lectura remota y descarga de archivos de configuración (`/boot/firmware/`, `/etc/`, `[HOME_REDACTED]`).
  * Mapeo de dependencias, scripts de arranque y árboles de directorios.
  * Generación de manifiestos y hashes de integridad SHA256.

### E. AGENT-AUDITOR (Nivel 9 - Integridad y Auditoría Continua)
* **Objetivo:** Registro estricto, secuencial y no repudiable de cada comando ejecutado en la bitácora técnica `COMMAND_EXECUTION_AUDIT.md`.
* **Permisos:**
  * Verificación obligatoria de códigos de salida (`$? == 0`).
  * Mantenimiento de la bitácora técnica tabular.

---

## 3. Matriz de Permisos por Recurso

| Recurso / Componente | AGENT-CORE | AGENT-NETWORK | AGENT-INTROSPECT | AGENT-TWIN-SYNC | AGENT-AUDITOR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `[HIL_WORKSPACE_REDACTED] HIL\` | R/W/X | R/W | R | R/W | R/W |
| `COMMAND_EXECUTION_AUDIT.md` | R/W | W (append) | W (append) | W (append) | R/W (Admin) |
| SSH Shell / Claves (`~/.ssh/`) | R/W/X | R/W/X | R/X | R/X | R |
| Raspberry Pi `/proc/`, `/sys/` | R | R | R | R | R |
| Raspberry Pi Kernel RT Params | **PROHIBIDO** | **PROHIBIDO** | **SOLO LECTURA** | **SOLO LECTURA** | **PROHIBIDO** |
| Raspberry Pi NetworkManager (`nmcli`) | R/W/X | R/W/X | R | R | R |
| `Digital_Twin_Workspace/` | R/W/X | R | R | R/W/X | R |
