# FUNDAMENTOS Y DIRECTRICES DE DETERMINISMO RTOS (DETERMINISTIC_RTOS.md)

## 1. El Parche PREEMPT_RT en Debian aarch64
El kernel `6.18.34+rpt-rpi-v8-rt` transforma el kernel estándar monolítico de Linux en un sistema operativo de tiempo real duro mediante:
* **Spinlocks Dormilones (`rt_mutex`):** Reemplaza los spinlocks tradicionales del kernel por mutexes con soporte para herencia de prioridad (*Priority Inheritance Protocol*), eliminando la inversión de prioridad descontrolada.
* **Manejadores de Interrupciones en Hilos:** Todas las interrupciones hardware (`top-half`) excepto aquellas explícitamente marcadas como `IRQF_NO_THREAD` se ejecutan como hilos de kernel planificables con prioridades configurables vía `chrt`.
* **Desactivación de Preempción Mínima:** Las secciones con deshabilitación de preempción se reducen a lo estrictamente necesario para la coherencia de hardware.

## 2. Axiomas de Aislamiento de Silicio
Para garantizar que un hilo de control HIL no sufra jitter superior a 15 microsegundos:
1. `isolcpus`: Aísla núcleos del planificador general de Linux.
2. `nohz_full`: Detiene el tick del temporizador del kernel en núcleos con un único hilo ejecutable.
3. `rcu_nocbs`: Descarga el procesamiento de callbacks RCU a núcleos de housekeeping.
4. `scaling_governor=performance`: Bloquea los multiplicadores de frecuencia de reloj en su valor máximo, eliminando latencias por cambio de estado de energía C-States/P-States.

## 3. Políticas de Memoria
* Bloqueo de páginas virtuales en RAM física mediante `mlockall(MCL_CURRENT | MCL_FUTURE)`.
* Prefaulting de la pila para prevenir *page faults* dentro de la sección crítica de tiempo real.
