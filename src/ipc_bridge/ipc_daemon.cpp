#include <iostream>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <mosquitto.h>
#include <cstring>
#include <signal.h>
#include <time.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include "../rt_core/SharedState.hpp"

static std::atomic<bool> g_running{true};
static HILSharedMemory* shm_ptr = nullptr;
static std::atomic<uint64_t> g_command_sequence{0};

// Manejador de señales para parada ordenada
static void signal_handler(int sig) {
    (void)sig;
    g_running.store(false, std::memory_order_relaxed);
}

// Obtener tiempo monótono en nanosegundos
static inline uint64_t get_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (static_cast<uint64_t>(ts.tv_sec) * 1000000000ULL) + static_cast<uint64_t>(ts.tv_nsec);
}

// Callback de Conexión MQTT
void on_connect(struct mosquitto *mosq, void *userdata, int rc) {
    (void)userdata;
    if (rc == 0) {
        std::cout << "[+] Conectado exitosamente al broker MQTT Mosquitto." << std::endl;
        mosquitto_subscribe(mosq, nullptr, "hil/command", 1);
        mosquitto_subscribe(mosq, nullptr, "hil/emergency_stop", 1);
        std::cout << "[+] Suscrito a temas: 'hil/command' y 'hil/emergency_stop'." << std::endl;
    } else {
        std::cerr << "[-] Conexión rechazada por el broker MQTT. Código: " << rc << std::endl;
    }
}

// Callback de Desconexión MQTT (Resiliencia ante caídas del broker)
void on_disconnect(struct mosquitto *mosq, void *userdata, int rc) {
    (void)mosq;
    (void)userdata;
    if (rc != 0) {
        std::cerr << "[!] Desconexión inesperada de MQTT (rc=" << rc << "). El demonio reintentará en segundo plano..." << std::endl;
    }
}

// Callback de Mensajes MQTT -> Encolamiento en Memoria Compartida
void on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message) {
    (void)mosq;
    (void)userdata;

    if (!shm_ptr || !message || !message->payload) {
        return;
    }

    HILCommand cmd;
    std::memset(&cmd, 0, sizeof(cmd));
    cmd.sequence_id = g_command_sequence.fetch_add(1, std::memory_order_relaxed);
    cmd.timestamp_ns = get_time_ns();
    cmd.control_flags = CTRL_FLAG_NONE;

    const char* topic = message->topic;
    const char* payload = static_cast<const char*>(message->payload);

    if (std::strcmp(topic, "hil/emergency_stop") == 0) {
        cmd.action_id = 999;
        cmd.control_flags = CTRL_FLAG_EMERGENCY_STOP;
        cmd.target_speed_rad_s = 0.0f;
    } else {
        // Parsear payload básico (formato numérico o simple: ej. "150.5" o "cmd:1,speed:100.0")
        float speed = 0.0f;
        if (std::strstr(payload, "speed")) {
            const char* s_ptr = std::strstr(payload, "speed");
            std::sscanf(s_ptr, "speed\":%f", &speed);
            if (speed == 0.0f) std::sscanf(s_ptr, "speed:%f", &speed);
        } else {
            speed = std::strtof(payload, nullptr);
        }

        cmd.action_id = 1;
        cmd.control_flags = CTRL_FLAG_MOTOR_ENABLE;
        cmd.target_speed_rad_s = speed;
    }

    // Insertar en la cola Lock-Free
    if (!shm_ptr->web_to_hardware.push(cmd)) {
        shm_ptr->header.dropped_commands_count.fetch_add(1, std::memory_order_relaxed);
        std::cerr << "[WARN] Buffer de comandos saturado. Comando descartado (seq=" << cmd.sequence_id << ")." << std::endl;
    }
}

int main() {
    // 1. Configuración de señales POSIX
    struct sigaction sa;
    std::memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGTERM, &sa, nullptr);

    // 2. Apertura e Inicialización Idempotente de Memoria Compartida
    int shm_fd = shm_open("/hil_shm", O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) {
        std::cerr << "[FATAL] No se pudo abrir/crear /dev/shm/hil_shm en IPC Daemon." << std::endl;
        return 1;
    }
    ftruncate(shm_fd, sizeof(HILSharedMemory));
    shm_ptr = static_cast<HILSharedMemory*>(
        mmap(nullptr, sizeof(HILSharedMemory), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0)
    );

    if (shm_ptr == MAP_FAILED) {
        std::cerr << "[FATAL] Error en mmap de memoria compartida." << std::endl;
        close(shm_fd);
        return 1;
    }

    // Inicialización segura sin destruir la memoria si ya estaba activa
    uint32_t expected = 0;
    if (shm_ptr->header.is_initialized.compare_exchange_strong(expected, 1, std::memory_order_acq_rel)) {
        shm_ptr->header.magic = HIL_SHM_MAGIC;
        shm_ptr->header.version = HIL_PROTOCOL_VERSION;
        shm_ptr->header.rt_heartbeat_tick.store(0, std::memory_order_relaxed);
        shm_ptr->header.ipc_heartbeat_tick.store(0, std::memory_order_relaxed);
        shm_ptr->header.dropped_commands_count.store(0, std::memory_order_relaxed);
        shm_ptr->header.dropped_telemetry_count.store(0, std::memory_order_relaxed);
        shm_ptr->web_to_hardware.reset();
        shm_ptr->hardware_to_web.reset();
        std::cout << "[+] Segmento /hil_shm creado e inicializado limpiamente." << std::endl;
    } else {
        std::cout << "[+] Segmento /hil_shm existente detectado. Acoplado sin reinicialización destructiva." << std::endl;
    }

    // 3. Inicialización del Cliente MQTT con Resiliencia y Reconexión Automática
    mosquitto_lib_init();
    struct mosquitto *mosq = mosquitto_new("HIL_IPC_Daemon_Bridge", true, nullptr);
    if (!mosq) {
        std::cerr << "[FATAL] No se pudo instanciar cliente Mosquitto." << std::endl;
        munmap(shm_ptr, sizeof(HILSharedMemory));
        close(shm_fd);
        mosquitto_lib_cleanup();
        return 1;
    }

    mosquitto_connect_callback_set(mosq, on_connect);
    mosquitto_disconnect_callback_set(mosq, on_disconnect);
    mosquitto_message_callback_set(mosq, on_message);

    // Configurar reconexión automática con exponential backoff (min: 1s, max: 15s)
    mosquitto_reconnect_delay_set(mosq, 1, 15, true);

    // Conexión no bloqueante asíncrona
    int rc = mosquitto_connect_async(mosq, "localhost", 1883, 60);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "[WARN] mosquitto_connect_async retornó código: " << rc << ". El demonio reintentará en el bucle." << std::endl;
    }

    // Iniciar hilo de red en background de Mosquitto
    mosquitto_loop_start(mosq);
    std::cout << "[+] Demonio IPC en línea. Puente bidireccional MQTT <-> SHM activo." << std::endl;

    // 4. Bucle Principal de Telemetría (Extracción SHM -> Publicación MQTT)
    char telem_buffer[256];
    while (g_running.load(std::memory_order_relaxed)) {
        // Despachar telemetría producida por el lazo RT hacia el broker MQTT
        HILTelemetry telem;
        int processed = 0;
        while (shm_ptr->hardware_to_web.pop(telem) && processed < 64) {
            std::snprintf(telem_buffer, sizeof(telem_buffer),
                "{\"seq\":%llu,\"ts\":%llu,\"speed\":%.2f,\"current\":%.2f,\"v_bus\":%.1f,\"temp\":%.1f,\"lat_ns\":%u,\"err\":%u}",
                static_cast<unsigned long long>(telem.sequence_id),
                static_cast<unsigned long long>(telem.timestamp_ns),
                telem.measured_speed_rad_s,
                telem.measured_current_a,
                telem.measured_voltage_v,
                telem.measured_temp_c,
                telem.cycle_latency_ns,
                telem.error_code
            );

            mosquitto_publish(mosq, nullptr, "hil/telemetry", static_cast<int>(std::strlen(telem_buffer)), telem_buffer, 0, false);
            processed++;
        }

        // Actualizar heartbeat del Demonio IPC
        shm_ptr->header.ipc_heartbeat_tick.fetch_add(1, std::memory_order_relaxed);

        // Dormir 10 ms en el dominio de housekeeping (Cores 0/1)
        usleep(10000);
    }

    // 5. Apagado Limpio y Liberación de Recursos
    std::cout << "[+] Deteniendo demonio IPC..." << std::endl;
    mosquitto_loop_stop(mosq, true);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();

    munmap(shm_ptr, sizeof(HILSharedMemory));
    close(shm_fd);
    std::cout << "[+] Demonio IPC finalizado de forma ordenada." << std::endl;
    return 0;
}
