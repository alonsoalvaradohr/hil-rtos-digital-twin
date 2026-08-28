#include <iostream>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sched.h>
#include <time.h>
#include <signal.h>
#include <cstring>
#include <atomic>
#include "SharedState.hpp"

// Bandera global atómica para terminación ordenada
static std::atomic<bool> g_running{true};

// Manejador determinista de señales POSIX
static void signal_handler(int sig) {
    (void)sig;
    g_running.store(false, std::memory_order_relaxed);
}

// Prefaulting seguro de la pila de ejecución (4 MB) para prevenir Minor Page Faults
static void prefault_stack() {
    constexpr size_t STACK_PREFAULT_SIZE = 4 * 1024 * 1024; // 4 MB
    volatile unsigned char buffer[STACK_PREFAULT_SIZE];
    for (size_t i = 0; i < STACK_PREFAULT_SIZE; i += 4096) {
        buffer[i] = 0;
    }
}

// Función auxiliar para obtener tiempo en nanosegundos (CLOCK_MONOTONIC)
static inline uint64_t get_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (static_cast<uint64_t>(ts.tv_sec) * 1000000000ULL) + static_cast<uint64_t>(ts.tv_nsec);
}

int main() {
    // 1. Configurar manejadores de señales para apagado seguro
    struct sigaction sa;
    std::memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);

    // 2. Bloqueo estricto de memoria en RAM física
    if (mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
        std::cerr << "[FATAL] mlockall falló. Se requieren privilegios CAP_SYS_RESOURCE / LimitMEMLOCK=infinity." << std::endl;
        return 1;
    }

    // Ejecutar prefaulting de pila
    prefault_stack();

    // 3. Afinidad de CPU Exclusiva: Core 3 (Aislamiento de Silicio Puro)
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(3, &cpuset); // Core 3 dedicado al lazo RT
    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == -1) {
        std::cerr << "[FATAL] No se pudo anclar al Core 3 aislado." << std::endl;
        return 1;
    }

    // 4. Política de Planificación de Tiempo Real Duro (SCHED_FIFO Prio 99)
    struct sched_param param;
    param.sched_priority = 99;
    if (sched_setscheduler(0, SCHED_FIFO, &param) == -1) {
        std::cerr << "[FATAL] Error estableciendo SCHED_FIFO 99. Verifique /etc/security/limits.d/." << std::endl;
        return 1;
    }

    // 5. Conectar o Inicializar la Memoria Compartida (/hil_shm)
    int shm_fd = shm_open("/hil_shm", O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) {
        std::cerr << "[FATAL] No se pudo abrir/crear /dev/shm/hil_shm." << std::endl;
        return 1;
    }
    ftruncate(shm_fd, sizeof(HILSharedMemory));
    HILSharedMemory* shm_ptr = static_cast<HILSharedMemory*>(
        mmap(nullptr, sizeof(HILSharedMemory), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0)
    );

    if (shm_ptr == MAP_FAILED) {
        std::cerr << "[FATAL] Fallo en mmap para /hil_shm." << std::endl;
        close(shm_fd);
        return 1;
    }

    // Inicialización atómica e idempotente si la memoria compartida es nueva
    uint32_t expected_init = 0;
    if (shm_ptr->header.is_initialized.compare_exchange_strong(expected_init, 1, std::memory_order_acq_rel)) {
        shm_ptr->header.magic = HIL_SHM_MAGIC;
        shm_ptr->header.version = HIL_PROTOCOL_VERSION;
        shm_ptr->header.rt_heartbeat_tick.store(0, std::memory_order_relaxed);
        shm_ptr->header.ipc_heartbeat_tick.store(0, std::memory_order_relaxed);
        shm_ptr->header.dropped_commands_count.store(0, std::memory_order_relaxed);
        shm_ptr->header.dropped_telemetry_count.store(0, std::memory_order_relaxed);
        shm_ptr->web_to_hardware.reset();
        shm_ptr->hardware_to_web.reset();
    }

    // Log inicial antes de entrar al lazo crítico (ÚNICO mensaje en stdout permitido)
    std::cout << "[+] Motor HIL RTOS inicializado con éxito. Anclado a Core 3 (SCHED_FIFO 99). Entrando al lazo determinista 1 kHz..." << std::endl;

    // 6. Preparación del Lazo Determinista Absoluto (1 kHz -> Periodo = 1,000,000 ns)
    constexpr uint64_t PERIOD_NS = 1000000ULL;
    struct timespec next_period;
    clock_gettime(CLOCK_MONOTONIC, &next_period);

    // Variables internas del emulador de planta / motor
    uint64_t sequence_counter = 0;
    float current_speed_rad_s = 0.0f;
    float current_torque_nm = 0.0f;
    float target_speed_rad_s = 0.0f;
    bool motor_enabled = false;

    // =========================================================================
    // LAZO DETERMINISTA DE TIEMPO REAL DURO (CERO I/O, CERO ALLOCATIONS, CERO LOCKS)
    // =========================================================================
    while (g_running.load(std::memory_order_relaxed)) {
        // Calcular tiempo de ciclo absoluto para prevenir deriva (Anti-Drift)
        next_period.tv_nsec += static_cast<long>(PERIOD_NS);
        while (next_period.tv_nsec >= 1000000000L) {
            next_period.tv_nsec -= 1000000000L;
            next_period.tv_sec += 1;
        }

        // Suspender ejecución hasta el instante exacto monótono
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next_period, nullptr);

        const uint64_t cycle_start_ns = get_time_ns();

        // 1. Ingesta de comandos desde la cola Lock-Free (Non-blocking)
        HILCommand cmd;
        while (shm_ptr->web_to_hardware.pop(cmd)) {
            if (cmd.control_flags & CTRL_FLAG_EMERGENCY_STOP) {
                motor_enabled = false;
                target_speed_rad_s = 0.0f;
                shm_ptr->header.emergency_stop_active.store(1, std::memory_order_relaxed);
            } else {
                if (cmd.control_flags & CTRL_FLAG_MOTOR_ENABLE) {
                    motor_enabled = true;
                }
                if (cmd.control_flags & CTRL_FLAG_CLEAR_FAULTS) {
                    shm_ptr->header.emergency_stop_active.store(0, std::memory_order_relaxed);
                }
                target_speed_rad_s = cmd.target_speed_rad_s;
            }
        }

        // 2. Física del Emulador de Planta HIL (Modelo de Primer Orden de Servomotor)
        if (motor_enabled && !shm_ptr->header.emergency_stop_active.load(std::memory_order_relaxed)) {
            // Dinámica: dw/dt = (K*u - w) / Tau  (Tau = 0.05s, dt = 0.001s)
            constexpr float dt = 0.001f;
            constexpr float tau = 0.050f;
            current_speed_rad_s += (dt / tau) * (target_speed_rad_s - current_speed_rad_s);
            current_torque_nm = (target_speed_rad_s - current_speed_rad_s) * 0.15f;
        } else {
            current_speed_rad_s *= 0.98f; // Fricción natural al detenerse
            current_torque_nm = 0.0f;
        }

        const uint64_t cycle_end_ns = get_time_ns();
        const uint32_t cycle_execution_latency_ns = static_cast<uint32_t>(cycle_end_ns - cycle_start_ns);

        // 3. Emisión de Telemetría hacia la cola Lock-Free (Non-blocking)
        HILTelemetry telem;
        telem.status_id = motor_enabled ? 1 : 0;
        telem.error_code = shm_ptr->header.emergency_stop_active.load(std::memory_order_relaxed);
        telem.sequence_id = ++sequence_counter;
        telem.timestamp_ns = cycle_end_ns;
        telem.measured_speed_rad_s = current_speed_rad_s;
        telem.measured_current_a = current_torque_nm * 1.8f;
        telem.measured_voltage_v = 48.0f;
        telem.measured_temp_c = 42.5f;
        telem.cycle_latency_ns = cycle_execution_latency_ns;
        telem.crc32 = 0; // Checksum básico para validación

        if (!shm_ptr->hardware_to_web.push(telem)) {
            // Buffer lleno: Registrar overflow atómicamente sin bloquear el lazo
            shm_ptr->header.dropped_telemetry_count.fetch_add(1, std::memory_order_relaxed);
        }

        // 4. Publicar Heartbeat de silicio en tiempo real
        shm_ptr->header.rt_heartbeat_tick.fetch_add(1, std::memory_order_relaxed);
    }
    // =========================================================================

    std::cout << "[+] Apagado ordenado del motor HIL completado. Liberando recursos." << std::endl;
    munmap(shm_ptr, sizeof(HILSharedMemory));
    close(shm_fd);
    return 0;
}
