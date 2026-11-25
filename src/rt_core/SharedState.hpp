// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
#ifndef SHARED_STATE_HPP
#define SHARED_STATE_HPP

#include "LockFreeQueue.hpp"
#include <cstdint>
#include <atomic>

// Constantes de Integridad de Memoria Compartida
constexpr uint64_t HIL_SHM_MAGIC = 0x48494C5F53484D32ULL; // "HIL_SHM2"
constexpr uint32_t HIL_PROTOCOL_VERSION = 0x00020000;      // Versión 2.0.0
constexpr size_t HIL_QUEUE_CAPACITY = 1024;                // Capacidad de 1024 items (~1.024s buffer a 1kHz)

// Banderas de Control y Estados de Emergencia
enum HILControlFlags : uint32_t {
    CTRL_FLAG_NONE           = 0x00000000,
    CTRL_FLAG_MOTOR_ENABLE   = 0x00000001,
    CTRL_FLAG_CLEAR_FAULTS   = 0x00000002,
    CTRL_FLAG_CALIBRATE      = 0x00000004,
    CTRL_FLAG_EMERGENCY_STOP = 0x80000000
};

// Estructura Universal de Comandos de Alta Resiliencia (IPC -> RT Core)
struct alignas(16) HILCommand {
    uint32_t action_id;              // Identificador de acción
    uint32_t control_flags;          // Banderas de control (HILControlFlags)
    uint64_t sequence_id;            // Número de secuencia estrictamente monótono
    uint64_t timestamp_ns;          // Marca de tiempo CLOCK_MONOTONIC en nanosegundos
    float target_speed_rad_s;        // Velocidad objetivo (rad/s)
    float target_torque_nm;          // Torque objetivo (Nm)
    float target_voltage_v;          // Voltaje objetivo (V)
    uint32_t crc32;                  // Checksum de integridad
};

// Estructura Universal de Telemetría Determinista (RT Core -> IPC)
struct alignas(16) HILTelemetry {
    uint32_t status_id;              // Código de estado operativo
    uint32_t error_code;             // Código de error / diagnóstico
    uint64_t sequence_id;            // Número de secuencia del lazo RT
    uint64_t timestamp_ns;          // Marca de tiempo de ejecución del ciclo RT
    float measured_speed_rad_s;      // Velocidad angular medida
    float measured_current_a;        // Corriente de fase medida (A)
    float measured_voltage_v;        // Voltaje de bus DC medido (V)
    float measured_temp_c;           // Temperatura de etapa de potencia (°C)
    uint32_t cycle_latency_ns;       // Latencia de ciclo de cálculo medida en silicio (ns)
    uint32_t crc32;                  // Checksum de integridad
};

// Cabecera de Sincronización e Idempotencia de Memoria Compartida
struct alignas(64) HILSharedMemoryHeader {
    uint64_t magic;                                  // Magic number HIL_SHM_MAGIC
    uint32_t version;                                // Protocol version
    std::atomic<uint32_t> is_initialized{0};         // Bandera atómica de inicialización completa

    // Latidos de vida independientes (Heartbeats para detección de caídas)
    alignas(64) std::atomic<uint64_t> rt_heartbeat_tick{0};
    alignas(64) std::atomic<uint64_t> ipc_heartbeat_tick{0};

    // Contadores de diagnóstico y desbordamiento
    alignas(64) std::atomic<uint64_t> dropped_commands_count{0};
    alignas(64) std::atomic<uint64_t> dropped_telemetry_count{0};
    alignas(64) std::atomic<uint32_t> emergency_stop_active{0};
};

// Mapa Maestro de la Memoria Compartida (/dev/shm/hil_shm)
struct alignas(64) HILSharedMemory {
    HILSharedMemoryHeader header;

    // Colas circulares SPSC Lock-Free alineadas en memoria
    alignas(64) LockFreeQueue<HILCommand, HIL_QUEUE_CAPACITY> web_to_hardware;
    alignas(64) LockFreeQueue<HILTelemetry, HIL_QUEUE_CAPACITY> hardware_to_web;
};

#endif // SHARED_STATE_HPP
