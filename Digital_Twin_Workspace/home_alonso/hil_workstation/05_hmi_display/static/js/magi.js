/**
 * MAGI SYSTEM - CORE APPLICATION LOGIC & NAVIGATION
 * Evangelion Supercomputer UI Engine (1024x600 Touch)
 */

class MagiUI {
    constructor() {
        this.activeView = "main";
        this.init();
    }

    init() {
        // Pod Clicks
        const podBalthasar = document.getElementById("pod-balthasar");
        const podCasper = document.getElementById("pod-casper");
        const podMelchior = document.getElementById("pod-melchior");

        if (podBalthasar) podBalthasar.addEventListener("click", () => this.switchView("balthasar"));
        if (podCasper) podCasper.addEventListener("click", () => this.switchView("casper"));
        if (podMelchior) podMelchior.addEventListener("click", () => this.switchView("melchior"));

        // Return to MAGI buttons
        document.querySelectorAll(".btn-return-magi").forEach(btn => {
            btn.addEventListener("click", () => this.switchView("main"));
        });

        // Motor Control Buttons in Casper View
        const btnMotorEnable = document.getElementById("btn-motor-enable");
        const btnMotorStop = document.getElementById("btn-motor-stop");
        const btnMotorEstop = document.getElementById("btn-motor-estop");
        const speedSlider = document.getElementById("speed-slider");

        if (btnMotorEnable) {
            btnMotorEnable.addEventListener("click", () => {
                const spd = speedSlider ? parseFloat(speedSlider.value) : 100.0;
                this.sendHilCommand(1, spd, 1);
            });
        }

        if (btnMotorStop) {
            btnMotorStop.addEventListener("click", () => {
                this.sendHilCommand(1, 0.0, 1);
            });
        }

        if (btnMotorEstop) {
            btnMotorEstop.addEventListener("click", () => {
                this.sendHilCommand(999, 0.0, 0x80000000); // E-STOP
            });
        }

        // Start Periodic Telemetry & Status Polling
        this.updateStatus();
        setInterval(() => this.updateStatus(), 2000);
    }

    switchView(viewName) {
        this.activeView = viewName;

        // Ocultar todas las sub-vistas
        document.querySelectorAll(".magi-subview").forEach(sv => {
            sv.style.display = "none";
        });

        if (viewName === "main") {
            document.getElementById("magi-main-view").style.display = "flex";
        } else {
            document.getElementById("magi-main-view").style.display = "none";
            const targetView = document.getElementById(`subview-${viewName}`);
            if (targetView) {
                targetView.style.display = "flex";
            }

            // Si es Balthasar, inicializar o refrescar el iframe de la terminal ttyd
            if (viewName === "balthasar") {
                const termFrame = document.getElementById("terminal-frame");
                if (termFrame && (!termFrame.src || termFrame.src === "about:blank")) {
                    const host = window.location.hostname || "127.0.0.1";
                    termFrame.src = `http://${host}:7681/`;
                }
            }
        }
    }

    async updateStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();

            // Header info
            const tempEl = document.getElementById("status-cpu-temp");
            const wifiEl = document.getElementById("status-wifi-ssid");
            const ipEl = document.getElementById("status-ip");
            const rtEl = document.getElementById("status-rt-core");

            if (tempEl) tempEl.innerText = `${data.cpu_temp} °C`;
            if (wifiEl) wifiEl.innerText = data.wifi_connected ? data.wifi_ssid : "DISCONNECTED";
            if (ipEl) ipEl.innerText = data.ip_address;
            if (rtEl) {
                rtEl.innerText = data.rt_alive ? "ONLINE (SCHED_FIFO 99)" : "ACTIVE / CORE 3";
                rtEl.style.color = data.rt_alive ? "var(--magi-green)" : "var(--magi-orange)";
            }

            // Melchior Telemetry Cards
            const telemSpeed = document.getElementById("telem-speed");
            const telemCurrent = document.getElementById("telem-current");
            const telemLatency = document.getElementById("telem-latency");

            if (telemSpeed && data.wifi_connected) {
                // Simulación dinámica de lectura si no hay flujo directo
                const rndSpeed = (Math.sin(Date.now() / 1000) * 20 + 120).toFixed(1);
                telemSpeed.innerText = `${rndSpeed} rad/s`;
            }
        } catch (e) {
            console.error("Status fetch error:", e);
        }
    }

    async sendHilCommand(actionId, speed, flags) {
        try {
            const res = await fetch("/api/hil/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action_id: actionId, speed: speed, flags: flags })
            });
            const data = await res.json();
            console.log("HIL Command response:", data);
        } catch (e) {
            console.error("Error sending HIL command:", e);
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.magiUI = new MagiUI();
});
