# Contributing to HIL-RTOS Digital Twin

Thank you for your interest in contributing to **HIL-RTOS Digital Twin & Real-Time Hypervisor (Raspberry Pi 5 PREEMPT_RT)**! We welcome contributions that uphold the principles of deterministic real-time computing, lock-free concurrency, and rigorous security boundaries.

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) (Contributor Covenant v2.1).

---

## Local Development & Environment Setup

HIL-RTOS Digital Twin combines deterministic C++ real-time IPC cores, Python automation/HMI bridges, and shell orchestration on Linux PREEMPT_RT platforms.

### Prerequisites

- **Python**: 3.10 or higher (`python --version`)
- **C++ Compiler**: GCC/Clang with C++17 support (`g++ -std=c++17`)
- **Kernel / Target**: Linux kernel with PREEMPT_RT patchset (recommended: Raspberry Pi 5 kernel 6.6+ RT)
- **Git**: 2.30 or higher

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alonsoalvaradohr/hil-rtos-digital-twin.git
   cd hil-rtos-digital-twin
   ```

2. **Environment Configuration (Zero Credentials Policy):**
   - Copy `.env.example` to your local environment configuration:
     ```bash
     cp .env.example .env
     ```
   - Populate local target IP, port, and test parameters as needed.
   - **CRITICAL**: Never commit `.env`, SSH private keys, Cloudflare tunnel tokens, or private network credentials. The `.gitignore` strictly protects these assets.

3. **Verify Script Syntax:**
   Verify Python and Shell syntax before submitting changes:
   ```bash
   python -m py_compile scripts/automation/*.py src/hmi_ui/*.py
   bash -n scripts/automation/*.sh scripts/*.sh
   ```

---

## RTOS & PREEMPT_RT Standards

Contributions touching real-time loops and IPC mechanisms must strictly adhere to deterministic principles:

1. **Lock-Free Concurrency**:
   - Zero mutex locking or unbounded blocking in real-time execution paths (Core 1).
   - Use atomic operations (`std::atomic`) and lock-free ringbuffers (`LockFreeQueue.hpp`).
2. **Deterministic Memory Management**:
   - Zero dynamic memory allocation (`malloc`, `new`, `std::vector::push_back`) in the real-time periodic loop. Pre-allocate all buffers at initialization.
3. **Task Priority & Affinity**:
   - Real-time threads must be configured with `SCHED_FIFO` or `SCHED_RR` and pinned to isolated CPU cores (`pthread_setaffinity_np`).
4. **Hardware-in-the-Loop Isolation**:
   - High-latency tasks (network I/O, HMI websocket streaming, logging) must run in userspace non-RT domains decoupled via shared memory (`/dev/shm`).

---

## Commit Guidelines (Conventional Commits)

We enforce semantic commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` Introduces a new feature or real-time capability.
- `fix:` Patches a bug, race condition, or latency regression.
- `docs:` Documentation modifications or architecture updates.
- `refactor:` Code refactoring without changing observable behavior.
- `test:` Adding, updating, or fixing HIL benchmarks or integration tests.
- `chore:` Maintenance tasks, dependency updates, governance adjustments.

*Example:* `feat(rt_core): optimize atomic memory fence in lock-free ringbuffer`

---

## Pull Request Process

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Verify all Python and Shell files pass syntax validation:
   ```bash
   python -m py_compile scripts/automation/*.py src/hmi_ui/*.py
   bash -n scripts/automation/*.sh scripts/*.sh
   ```
3. Ensure SPDX headers remain in place on all modified files:
   - Python / Shell:
     ```python
     # SPDX-License-Identifier: GPL-3.0-or-later
     # Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
     ```
   - C++:
     ```cpp
     // SPDX-License-Identifier: GPL-3.0-or-later
     // Copyright (C) 2024-2026 Alonso Alvarado Hernández <alonsoalvaradohr>
     ```
4. Verify that no private credentials, SSH passwords, or active tunnels are committed.
5. Open a Pull Request referencing the related issue or engineering ticket.
