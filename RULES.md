# REGLAS DE GOBERNANZA OPERACIONAL Y AXIOMAS DE SEGURIDAD (RULES.md)

## 1. Declaración de Misión y Filosofía
El presente documento establece el marco normativo inmutable para la operación de agentes autónomos y desarrolladores humanos en el entorno de desarrollo y validación **Hardware-in-the-Loop (HIL)** basado en **Raspberry Pi 5** con kernel de tiempo real (**SMP PREEMPT_RT Debian**).

La arquitectura HIL exige determinismo temporal estricto, resiliencia en comunicaciones y aislamiento riguroso entre tareas críticas de control y servicios de telemetría/gobernanza.

---

## 2. Axiomas Inmutables de Seguridad y Confinamiento

### Axioma 1: Confinamiento Local Absoluto
* **Regla:** El directorio raíz primario y exclusivo de trabajo en el host es `[HIL_WORKSPACE_REDACTED] HIL`.
* **Restricción:** Queda estrictamente prohibido generar archivos de gobernanza, bitácoras, volcados o scripts fuera de este árbol de directorios.

### Axioma 2: Preservación de la Integridad RTOS y Silicio
* **Regla:** Durante todas las fases de introspección, auditoría, sincronización y pruebas, los parámetros de aislamiento del kernel tienen estatus de **SOLO LECTURA**.
* **Parámetros Protegidos:**
  * Parámetros de aislamiento de núcleos (`isolcpus`, `nohz_full`, `rcu_nocbs`).
  * Gobernador de escalado de frecuencia de CPU (`cpufreq`, `scaling_governor`).
  * Prioridades de planificación de tiempo real (`SCHED_FIFO`, `SCHED_RR`, `rtprio`, `limits.conf`).
* **Justificación:** Prevenir jitter temporal, latencias no deterministas y pérdidas de sincronismo en simulaciones HIL.

### Axioma 3: Determinismo y Verificación de Código de Salida
* **Regla:** Toda acción ejecutada tanto en el host como en el target remoto debe verificar explícitamente su código de retorno (`$? == 0` / `$LASTEXITCODE -eq 0`).
* **Protocolo ante Fallos:** Si un comando no finaliza exitosamente, la ejecución debe pausar la secuencia dependiente, capturar `stderr`, registrar la falla en `COMMAND_EXECUTION_AUDIT.md` y activar la estrategia de pivotaje O-I-P-E-V-R.

### Axioma 4: Ejecución Desatendida y No Interactiva
* **Regla:** Queda prohibido el uso de prompts interactivos bloqueantes (ej. confirmaciones `yes/no`, ingreso manual de contraseñas por terminal interactiva).
* **Mecanismo:** Empleo de autenticación por llave pública SSH (`id_ed25519_hil`), elevación `sudo` no interactiva y scripts de automatización estructurados.

### Axioma 5: Veracidad Empírica (Ground Truth)
* **Regla:** Ningún dato técnico de hardware, red, memoria, particiones o servicios puede ser inferido o alucinado. Toda información reportada debe provenir directamente de la introspección remota en tiempo real mediante comandos de bajo nivel (`uname`, `lscpu`, `ip`, `lsblk`, `systemctl`, `cat /proc/*`, `cat /sys/*`).

### Axioma 6: Gemelo Digital Bidireccional pero Controlado
* **Regla:** El directorio `Digital_Twin_Workspace` funciona como el espejo fiel del estado del target. Los cambios hacia el target deben someterse a validación de sintaxis previa antes de su despliegue remoto.

---

## 3. Protocolo de Modificación y Despliegue
1. **Inspección Previa:** Verificar estado actual del recurso remoto.
2. **Respaldo Local:** Copiar estado previo a `Digital_Twin_Workspace/backups/`.
3. **Aplicación Determinista:** Ejecución remota vía SSH automatizado.
4. **Verificación de Salud:** Comprobación de servicio y latencia.
5. **Auditoría:** Registro inmediato en `COMMAND_EXECUTION_AUDIT.md`.
