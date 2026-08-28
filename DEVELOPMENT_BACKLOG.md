# BACKLOG DE DESARROLLO Y HOJA DE RUTA TÉCNICA (DEVELOPMENT BACKLOG)

**Proyecto:** Hipervisor Industrial Hardware-in-the-Loop (HIL-RTOS)  
**Versión Actual:** v6.1.0 (Arquitectura Base y HMI Operativa)  
**Próximo Milestone:** v7.0.0 (Inyección Física de Hardware y Buses en Tiempo Real)  

---

## 1. Visión Estratégica

La arquitectura base del software, la separación de dominios de silicio, el motor determinista en C++ y la interfaz gráfica MAGI están completamente consolidados y certificados. La siguiente fase de evolución técnica se enfoca en la interconexión con hardware físico externo mediante los buses de alta velocidad del SoC Broadcom BCM2712 y el Southbridge RP1 (GPIO, SPI DMA, I2C, CAN-FD y PWM).

---

## 2. Matriz de Épicas y Tareas Técnicas Priorizadas

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

---

## 3. Especificaciones Técnicas y Ecuaciones de los Próximos Solucionadores HIL

### 3.1. Solucionador Numérico Runge-Kutta de 4to Orden (RK4) para Lazo de 10 kHz
Para emular plantas dinámicas rápidas (ej. motores síncronos de imanes permanentes PMSM con inductancias de fase en el orden de microhenrios), el integrador Euler de 1er orden actual será sustituido por el algoritmo Runge-Kutta clásico de 4to orden:

$$\frac{d\mathbf{x}}{dt} = \mathbf{f}(t, \mathbf{x}, \mathbf{u})$$

$$k_1 = \mathbf{f}(t_n, \mathbf{x}_n, \mathbf{u}_n)$$
$$k_2 = \mathbf{f}\left(t_n + \frac{h}{2}, \mathbf{x}_n + \frac{h}{2}k_1, \mathbf{u}_{n+1/2}\right)$$
$$k_3 = \mathbf{f}\left(t_n + \frac{h}{2}, \mathbf{x}_n + \frac{h}{2}k_2, \mathbf{u}_{n+1/2}\right)$$
$$k_4 = \mathbf{f}(t_n + h, \mathbf{x}_n + h k_3, \mathbf{u}_{n+1})$$

$$\mathbf{x}_{n+1} = \mathbf{x}_n + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4)$$

Donde $h = 100\,\mu\text{s}$ (paso de integración a 10 kHz) y el estado vectorial $\mathbf{x} = [i_d, i_q, \omega_r, \theta_r]^T$ representa las corrientes en el marco de referencia d-q de Park-Clarke y la dinámica mecánica del rotor.

### 3.2. Dimensionamiento del Buffer Circular DMA para Señales de Encoder
Para transmitir pulsos en cuadratura a 500 kHz sin sobrecargar la CPU, se utilizará el motor DMA de dispersión/recolección (*Scatter-Gather DMA*) del Southbridge RP1:

$$\text{Tasa de Transferencia} = 500{,}000\,\text{pulsos/s} \times 4\,\text{bytes/muestra} = 2.0\,\text{MB/s}$$
$$\text{Tamaño de Bloque DMA} = 4096\,\text{bytes} \implies \text{Periodo de Interrupción DMA} = \frac{4096}{2{,}000{,}000} \approx 2.048\,\text{ms}$$

Esto permite transferir ráfagas continuas de señales de posición angular directamente a los registros GPIO físicos sin ninguna intervención de los núcleos aislados de tiempo real duro.

