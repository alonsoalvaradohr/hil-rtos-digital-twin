sudo apt update && sudo apt install git bc bison flex libssl-dev make libncurses5-dev raspberrypi-kernel-headers libelf-dev -y
sudo apt update
sudo apt install git bc bison flex libssl-dev make libncurses-dev libelf-dev build-essential kmod dpkg-dev -y
mkdir ~/repositorio-kernel && cd ~/repositorio-kernel
git clone --depth 1 --branch rpi-6.6.y-rt https://github.com/raspberrypi/linux
cd linux
cd .
cd/
cd ./
cd ..
sudo apt update && sudo apt install tree -y
tree
tree -a
git clone --depth 1 --branch rpi-6.6.y-rt https://github.com/raspberrypi/linux
cd ~/repositorio-kernel
git clone --depth 1 --branch rpi-6.6.y https://github.com/raspberrypi/linux
cd linux
make bcm2712_defconfig
make menuconfig
git ls-remote --heads https://github.com/raspberrypi/linux | grep "\-rt"
cd ~/repositorio-kernel
rm -rf linux
cd ~/repositorio-kernel
git clone --depth 1 --branch rpi-6.6.y-rt-patched https://github.com/lemariva/RT-Linux-RPi.git linux
cd linux
make bcm2712_defconfig
make menuconfig
mkdir -p ~/hil_workstation/{00_kernel_build,01_system_tuning/{boot_config,irq_affinity,services},02_hardware_io/{dt_overlays,spi_dma,gpio_fast},03_hil_plant_model/solvers,04_ipc_shared_memory/{posix_shm,lock_free_queues},05_hmi_display/assets}
cd ~/hil_workstation/00_kernel_build
git clone --depth 1 --branch rpi-6.6.y https://github.com/raspberrypi/linux
cd linux
# 1. Identificar la versión exacta del Kernel de Raspberry Pi
KVER=$(make kernelversion)
echo "Tu versión de kernel base es: $KVER"
# 2. Buscar el parche oficial en los servidores de kernel.org
RT_URL="https://mirrors.edge.kernel.org/pub/linux/kernel/projects/rt/6.6/"
RT_FILE=$(curl -s $RT_URL | grep -o 'patch-'"$KVER"'-rt[0-9]*\.patch\.xz' | tail -1)
# 3. Validación y aplicación segura
if [ -z "$RT_FILE" ]; then     echo "ALERTA CRÍTICA: No se encontró un parche RT exacto para la versión $KVER en kernel.org."; else     echo "Parche encontrado: $RT_FILE. Iniciando descarga segura...";     wget "${RT_URL}${RT_FILE}";     echo "Aplicando parche de Tiempo Real al árbol de código...";     xzcat $RT_FILE | patch -p1; fi
curl -s https://mirrors.edge.kernel.org/pub/linux/kernel/projects/rt/6.6/ | grep -o 'patch-6\.6\.[0-9]\+-rt[0-9]\+\.patch\.xz' | sort -V | tail -5
curl -s https://mirrors.edge.kernel.org/pub/linux/kernel/projects/rt/6.6/ | grep -Eo 'patch-6\.6\.[0-9]+-rt[0-9]+\.patch\.xz' | sort -V | tail -n 5
curl -sL https://mirrors.edge.kernel.org/pub/linux/kernel/projects/rt/6.6/ | grep -Eo 'patch-6\.6\.[0-9]+-rt[0-9]+\.patch\.xz' | sort -V | tail -n 5
cd ~/hil_workstation/00_kernel_build/linux && rm -f .git/index.lock && git fsck
wget -qO- https://cdn.kernel.org/pub/linux/kernel/projects/rt/6.6/sha256sums.asc | awk '{print $2}' | grep "\.patch\.xz" | sort -V | tail -n 1
apt-cache search linux-image | grep "\-rt"
sudo apt install linux-image-rpi-v8-rt linux-headers-rpi-v8-rt -y
sudo cp /boot/firmware/config.txt ~/hil_workstation/01_system_tuning/boot_config/config_original.bak && sudo sh -c 'printf "\n[all]\nkernel=kernel8_rt.img\ninitramfs initramfs8_rt followkernel\n" >> /boot/firmware/config.txt' && tail -n 4 /boot/firmware/config.txt
sudo reboot
uname -v
sudo apt install cpufrequtils -y && sudo sh -c 'echo "GOVERNOR=\"performance\"" > /etc/default/cpufrequtils' && sudo systemctl restart cpufrequtils && cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
sudo bash -c 'cat << "EOF" > /etc/systemd/system/rt-cpu-governor.service
[Unit]
Description=Fijar Gobernador CPU a Performance para RTOS

[Service]
Type=oneshot
ExecStart=/bin/sh -c "for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $f; done"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF' && sudo systemctl daemon-reload && sudo systemctl enable --now rt-cpu-governor.service && cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
sudo sed -i -e 's/ isolcpus=[^ ]*//g' -e 's/ nohz_full=[^ ]*//g' -e 's/ rcu_nocbs=[^ ]*//g' /boot/firmware/cmdline.txt && sudo sed -i '1 s/$/ isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3/' /boot/firmware/cmdline.txt && cat /boot/firmware/cmdline.txt
sudo bash -c 'cat << "EOF" > /etc/systemd/system/rt-irq-affinity.service
[Unit]
Description=Enrutar IRQs a Cores 0 y 1 para aislar entorno HIL
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 3 > /proc/irq/default_smp_affinity; for d in /proc/irq/[0-9]*; do echo 3 > $d/smp_affinity 2>/dev/null; done; exit 0"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF' && sudo systemctl daemon-reload && sudo systemctl enable rt-irq-affinity.service && echo "[+] Aislamiento IRQ configurado y persistente."
sudo reboot
cat /sys/devices/system/cpu/isolated
sudo apt install rt-tests -y && cyclictest --version
sudo cyclictest -m -p 99 -a 2,3 -t 2 -i 1000 -D 1m -q
sudo bash -c 'cat << "EOF" > /etc/security/limits.d/99-realtime.conf
@alonso - rtprio 99
@alonso - memlock unlimited
EOF' && sudo groupadd -f realtime && sudo usermod -aG realtime alonso && echo "[+] Privilegios de Tiempo Real otorgados al usuario."
su - alonso -c "echo -n 'Max RT Priority: ' && ulimit -r && echo -n 'Max Locked Memory: ' && ulimit -l && df -hT /dev/shm"
mkdir -p ~/hil_workstation/02_ipc_core && cat << "EOF" > ~/hil_workstation/02_ipc_core/LockFreeQueue.hpp
#ifndef LOCK_FREE_QUEUE_HPP
#define LOCK_FREE_QUEUE_HPP

#include <atomic>
#include <cstdint>

// Patrón SPSC Lock-Free para IPC en Tiempo Real
template <typename T, size_t Size>
class LockFreeQueue {
private:
    T buffer[Size];
    std::atomic<size_t> head{0};
    std::atomic<size_t> tail{0};

public:
    // Llamado por el Productor (Ej. Lazo HIL)
    bool push(const T& item) {
        size_t current_tail = tail.load(std::memory_order_relaxed);
        size_t next_tail = (current_tail + 1) % Size;
        if (next_tail == head.load(std::memory_order_acquire)) {
            return false; // Buffer lleno (Evita bloqueo)
        }
        buffer[current_tail] = item;
        tail.store(next_tail, std::memory_order_release);
        return true;
    }

    // Llamado por el Consumidor (Ej. Hilo MQTT/GUI)
    bool pop(T& item) {
        size_t current_head = head.load(std::memory_order_relaxed);
        if (current_head == tail.load(std::memory_order_acquire)) {
            return false; // Buffer vacío (Evita bloqueo)
        }
        item = buffer[current_head];
        head.store((current_head + 1) % Size, std::memory_order_release);
        return true;
    }
};

#endif // LOCK_FREE_QUEUE_HPP
EOF

echo "[+] Plantilla C++ Lock-Free SPSC generada en ~/hil_workstation/02_ipc_core/LockFreeQueue.hpp"
sudo apt install mosquitto mosquitto-clients -y && sudo systemctl enable --now mosquitto && systemctl is-active mosquitto
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
sudo systemctl enable --now nodered.service && systemctl is-active nodered
cd ~/.node-red && npm install @node-red-contrib-themes/theme-collection @flowfuse/node-red-dashboard && sudo systemctl restart nodered && echo "[+] Nodos HMI y Tema Oscuro instalados. Servicio reiniciado."
sudo apt install chromium-browser x1ight- xdotool unclutter -y && echo "[+] Herramientas de visualización HMI instaladas con éxito."
sudo apt install chromium-browser -y
mkdir -p ~/.config/autostart && cat << "EOF" > ~/.config/autostart/hmi-kiosk.desktop
[Desktop Entry]
Type=Application
Name=HMI Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --ozone-platform=wayland http://127.0.0.1:1880/dashboard
X-GNOME-Autostart-enabled=true
EOF

echo "[+] Regla de arranque en Modo Kiosko HMI inyectada exitosamente."
sudo apt install libmosquitto-dev build-essential cmake -y && cat << "EOF" > ~/hil_workstation/02_ipc_core/SharedState.hpp
#ifndef SHARED_STATE_HPP
#define SHARED_STATE_HPP

#include "LockFreeQueue.hpp"

// Estructura universal para comandos (Web -> Cores 2/3)
struct HILCommand {
    uint32_t action_id;
    float payload;
};

// Estructura universal para telemetría (Cores 2/3 -> Web)
struct HILTelemetry {
    uint32_t sensor_id;
    float value;
};

// Mapa exacto de la Memoria Compartida (/dev/shm)
struct HILSharedMemory {
    LockFreeQueue<HILCommand, 256> web_to_hardware;
    LockFreeQueue<HILTelemetry, 256> hardware_to_web;
};

#endif // SHARED_STATE_HPP
EOF

echo "[+] Dependencias de compilación instaladas y Estructura de Memoria Compartida generada."
cat << "EOF" > ~/hil_workstation/02_ipc_core/ipc_daemon.cpp
#include <iostream>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <mosquitto.h>
#include <cstring>
#include "SharedState.hpp"

HILSharedMemory* shm_ptr = nullptr;

// Callback: Se ejecuta cuando llega un mensaje desde la Interfaz Web (Node-RED)
void on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message) {
    if(shm_ptr) {
        HILCommand cmd;
        cmd.action_id = 1; // ID de prueba
        cmd.payload = 1.0f; // En el futuro aquí parsearemos el JSON real
        
        // Empujar a la cola atómica (Cores 2/3 leerán esto sin bloqueos)
        shm_ptr->web_to_hardware.push(cmd);
    }
}

int main() {
    // 1. Crear y mapear Memoria Compartida pura en RAM (tmpfs)
    int shm_fd = shm_open("/hil_shm", O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd, sizeof(HILSharedMemory));
    shm_ptr = (HILSharedMemory*)mmap(0, sizeof(HILSharedMemory), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);

    // Inicializar la estructura de colas Atómicas en memoria
    new (shm_ptr) HILSharedMemory();

    // 2. Conectar al cerebro IoT (Mosquitto MQTT)
    mosquitto_lib_init();
    struct mosquitto *mosq = mosquitto_new("HIL_IPC_Bridge", true, NULL);
    mosquitto_message_callback_set(mosq, on_message);
    
    if(mosquitto_connect(mosq, "localhost", 1883, 60) != MOSQ_ERR_SUCCESS) {
        std::cerr << "Error crítico: No se pudo conectar a MQTT" << std::endl;
        return 1;
    }
    
    // Suscribirse al tema de comandos
    mosquitto_subscribe(mosq, NULL, "hil/command", 0);
    std::cout << "[+] Puente IPC compilado e iniciado. Traductor MQTT <-> SHM activo." << std::endl;
    
    // Mantener el demonio vivo (Delegado al sistema operativo en Cores 0/1)
    mosquitto_loop_forever(mosq, -1, 1);
    
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    return 0;
}
EOF

g++ -O3 -Wall ~/hil_workstation/02_ipc_core/ipc_daemon.cpp -o ~/hil_workstation/02_ipc_core/ipc_daemon -lmosquitto -lrt && echo "[+] Compilación exitosa: Binario 'ipc_daemon' generado."
cat << "EOF" > ~/hil_workstation/02_ipc_core/rt_motor.cpp
#include <iostream>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sched.h>
#include "SharedState.hpp"

int main() {
    // 1. Bloquear memoria en RAM (Prevenir latencia de Page Faults)
    if (mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
        std::cerr << "Error: No se pudo bloquear la memoria en RAM." << std::endl;
        return 1;
    }

    // 2. Afinidad de CPU: Anclar al silicio aislado (Cores 2 y 3)
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(2, &cpuset);
    CPU_SET(3, &cpuset);
    if (sched_setaffinity(0, sizeof(cpu_set_t), &cpuset) == -1) {
        std::cerr << "Error: No se pudo anclar a los Cores 2/3." << std::endl;
        return 1;
    }

    // 3. Política de Tiempo Real: Prioridad Máxima (99)
    struct sched_param param;
    param.sched_priority = 99;
    if (sched_setscheduler(0, SCHED_FIFO, &param) == -1) {
        std::cerr << "Error: No se pudo establecer la prioridad RT 99." << std::endl;
        return 1;
    }

    // 4. Conectar a la Memoria Compartida (tmpfs / RAM)
    int shm_fd = shm_open("/hil_shm", O_RDWR, 0666);
    if (shm_fd == -1) {
        std::cerr << "Error: No se encontró la memoria compartida. Ejecuta el Demonio IPC primero." << std::endl;
        return 1;
    }
    HILSharedMemory* shm_ptr = (HILSharedMemory*)mmap(0, sizeof(HILSharedMemory), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);

    std::cout << "[+] Lazo HIL iniciado en Cores aislados (Prioridad FIFO 99)." << std::endl;

    // 5. Lazo de Control Determinista (1 kHz)
    HILCommand cmd;
    while (true) {
        // Leer de la cola Lock-Free (Operación atómica de latencia ultrabaja)
        if (shm_ptr->web_to_hardware.pop(cmd)) {
            std::cout << "[Cores 2/3] Señal IoT recibida! ID: " << cmd.action_id << std::endl;
            // Aquí en el futuro interactuaremos con el GPIO / SPI / I2C
        }
        
        // Simular el ciclo de muestreo de 1 milisegundo (Ts = 1ms)
        usleep(1000); 
    }

    return 0;
}
EOF

g++ -O3 -Wall ~/hil_workstation/02_ipc_core/rt_motor.cpp -o ~/hil_workstation/02_ipc_core/rt_motor -lrt && echo "[+] Compilación exitosa: Binario 'rt_motor' (Tiempo Real) generado."
sudo bash -c 'cat << "EOF" > /etc/systemd/system/hil-ipc.service
[Unit]
Description=HIL IPC Traductor (MQTT a RAM)
After=mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=alonso
ExecStart=/home/alonso/hil_workstation/02_ipc_core/ipc_daemon
Restart=always

[Install]
WantedBy=multi-user.target
EOF' && sudo bash -c 'cat << "EOF" > /etc/systemd/system/hil-rt.service
[Unit]
Description=HIL Motor de Tiempo Real (Cores 2 y 3)
After=hil-ipc.service
Requires=hil-ipc.service

[Service]
Type=simple
User=alonso
LimitMEMLOCK=infinity
LimitRTPRIO=99
ExecStart=/home/alonso/hil_workstation/02_ipc_core/rt_motor
Restart=always

[Install]
WantedBy=multi-user.target
EOF' && sudo systemctl daemon-reload && sudo systemctl enable --now hil-ipc.service hil-rt.service && echo "[+] Orquestación finalizada. Sistema Nervioso HIL autónomo y en línea."
journalctl -u hil-rt.service -f
sudo shutdown  now
sudo shut down now
shutdown no
shutdown now
