// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
#ifndef LOCK_FREE_QUEUE_HPP
#define LOCK_FREE_QUEUE_HPP

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <type_traits>

/**
 * @brief Cola Circular SPSC (Single-Producer Single-Consumer) Lock-Free de Grado Industrial / Aeroespacial.
 * @tparam T Tipo de dato a almacenar (debe ser trivialmente copiable para evitar llamadas a constructores no deterministas).
 * @tparam Size Capacidad máxima del buffer circular (OBLIGATORIAMENTE potencia de 2).
 * 
 * @details
 * - Alineación estricta a 64 bytes (`alignas(64)`) para anular colisiones por False Sharing en la caché L1/L2 de ARM64 (Cortex-A76).
 * - Aritmética de índices optimizada a nivel de instrucciones con enmascaramiento binario bitwise `& (Size - 1)`.
 * - Sincronización explícita mediante barreras Acquire-Release conformes al modelo de memoria débil (Weak Memory Model) de ARM.
 */
template <typename T, size_t Size>
class LockFreeQueue {
    static_assert((Size > 1) && ((Size & (Size - 1)) == 0), 
                  "CRITICAL: LockFreeQueue Size debe ser una potencia de 2 para permitir enmascaramiento bitwise!");
    static_assert(std::is_trivially_copyable<T>::value, 
                  "CRITICAL: El tipo de dato T debe ser Trivially Copyable para garantizar determinismo en tiempo real.");

private:
    static constexpr size_t INDEX_MASK = Size - 1;

    // Buffer de almacenamiento alineado a línea de caché
    alignas(64) T buffer[Size];

    // Punteros atómicos aislados en líneas de caché independientes (64 bytes)
    alignas(64) std::atomic<size_t> head{0};
    alignas(64) std::atomic<size_t> tail{0};

public:
    LockFreeQueue() noexcept = default;
    ~LockFreeQueue() noexcept = default;

    // Prohibir copia y movimiento para integridad de memoria compartida
    LockFreeQueue(const LockFreeQueue&) = delete;
    LockFreeQueue& operator=(const LockFreeQueue&) = delete;
    LockFreeQueue(LockFreeQueue&&) = delete;
    LockFreeQueue& operator=(LockFreeQueue&&) = delete;

    /**
     * @brief Inserta un elemento en la cola (Llamado EXCLUSIVAMENTE por el Productor).
     * @param item Referencia al elemento a insertar.
     * @return true si la inserción fue exitosa, false si el buffer está saturado.
     */
    bool push(const T& item) noexcept {
        const size_t current_tail = tail.load(std::memory_order_relaxed);
        const size_t next_tail = (current_tail + 1) & INDEX_MASK;

        // Verificar si la cola está llena sincronizando con el head del consumidor
        if (next_tail == head.load(std::memory_order_acquire)) {
            return false; // Buffer lleno (No bloqueante)
        }

        buffer[current_tail] = item;

        // Publicar el nuevo elemento con semántica Release
        tail.store(next_tail, std::memory_order_release);
        return true;
    }

    /**
     * @brief Extrae un elemento de la cola (Llamado EXCLUSIVAMENTE por el Consumidor).
     * @param item Referencia donde se copiará el elemento extraído.
     * @return true si se extrajo un elemento, false si la cola está vacía.
     */
    bool pop(T& item) noexcept {
        const size_t current_head = head.load(std::memory_order_relaxed);

        // Verificar si la cola está vacía sincronizando con el tail del productor
        if (current_head == tail.load(std::memory_order_acquire)) {
            return false; // Buffer vacío (No bloqueante)
        }

        item = buffer[current_head];

        // Liberar la celda con semántica Release para el productor
        head.store((current_head + 1) & INDEX_MASK, std::memory_order_release);
        return true;
    }

    /**
     * @brief Retorna true si la cola está vacía en el momento de la consulta.
     */
    bool empty() const noexcept {
        return head.load(std::memory_order_relaxed) == tail.load(std::memory_order_relaxed);
    }

    /**
     * @brief Retorna la capacidad total de la cola.
     */
    static constexpr size_t capacity() noexcept {
        return Size - 1; // Un espacio se reserva para distinguir lleno de vacío
    }

    /**
     * @brief Reinicializa los punteros de la cola (Solo invocar bajo exclusión mutua o inicialización).
     */
    void reset() noexcept {
        head.store(0, std::memory_order_relaxed);
        tail.store(0, std::memory_order_relaxed);
    }
};

#endif // LOCK_FREE_QUEUE_HPP
