/**
 * MAGI SYSTEM - TOUCH NETWORK & BLUETOOTH MANAGER
 * Sanitized for Chromium Kiosk (Zero Unicode Tofu, NERV Style)
 */

class MagiNetwork {
    constructor() {
        this.modal = document.getElementById("network-modal");
        this.wifiListContainer = document.getElementById("wifi-network-list");
        this.btListContainer = document.getElementById("bt-device-list");
        this.selectedSSID = null;
        this.init();
    }

    init() {
        const btnNet = document.getElementById("btn-open-network");
        if (btnNet) {
            btnNet.addEventListener("click", () => this.open());
        }

        const btnClose = document.getElementById("btn-close-network");
        if (btnClose) {
            btnClose.addEventListener("click", () => this.close());
        }

        const tabWifi = document.getElementById("tab-btn-wifi");
        const tabBt = document.getElementById("tab-btn-bt");

        if (tabWifi) {
            tabWifi.addEventListener("click", () => this.switchTab("wifi"));
        }
        if (tabBt) {
            tabBt.addEventListener("click", () => this.switchTab("bluetooth"));
        }

        const btnScanWifi = document.getElementById("btn-rescan-wifi");
        if (btnScanWifi) {
            btnScanWifi.addEventListener("click", () => this.scanWifi());
        }

        const btnConfirmConn = document.getElementById("btn-confirm-connect");
        if (btnConfirmConn) {
            btnConfirmConn.addEventListener("click", () => this.submitConnection());
        }

        const btnCancelConn = document.getElementById("btn-cancel-connect");
        if (btnCancelConn) {
            btnCancelConn.addEventListener("click", () => this.cancelConnectionPrompt());
        }
    }

    open() {
        if (this.modal) {
            this.modal.style.display = "flex";
            this.switchTab("wifi");
            this.scanWifi();
        }
    }

    close() {
        if (this.modal) {
            this.modal.style.display = "none";
        }
        this.cancelConnectionPrompt();
    }

    switchTab(tab) {
        const tabWifi = document.getElementById("tab-btn-wifi");
        const tabBt = document.getElementById("tab-btn-bt");
        const secWifi = document.getElementById("section-wifi");
        const secBt = document.getElementById("section-bluetooth");

        if (tab === "wifi") {
            tabWifi.classList.add("active");
            tabBt.classList.remove("active");
            secWifi.style.display = "block";
            secBt.style.display = "none";
        } else {
            tabBt.classList.add("active");
            tabWifi.classList.remove("active");
            secWifi.style.display = "none";
            secBt.style.display = "block";
            this.scanBluetooth();
        }
    }

    async scanWifi() {
        if (!this.wifiListContainer) return;
        this.wifiListContainer.innerHTML = "<div style='color: var(--magi-orange); padding: 12px;'>[+] ESCANEANDO ESPECTRO DE RADIO WI-FI...</div>";

        try {
            const res = await fetch("/api/wifi/scan");
            const data = await res.json();

            if (!data.success || !data.networks || data.networks.length === 0) {
                this.wifiListContainer.innerHTML = "<div style='color: #888; padding: 12px;'>No se detectaron redes inalambricas en el area.</div>";
                return;
            }

            this.wifiListContainer.innerHTML = "";
            data.networks.forEach(net => {
                const item = document.createElement("div");
                item.className = "wifi-item";

                const signalLevel = (net.signal >= 75) ? 4 : (net.signal >= 50) ? 3 : (net.signal >= 25) ? 2 : 1;
                const signalBarsHtml = `
                    <div class="signal-meter">
                        <span class="signal-bar bar-1 ${signalLevel >= 1 ? 'active' : ''}"></span>
                        <span class="signal-bar bar-2 ${signalLevel >= 2 ? 'active' : ''}"></span>
                        <span class="signal-bar bar-3 ${signalLevel >= 3 ? 'active' : ''}"></span>
                        <span class="signal-bar bar-4 ${signalLevel >= 4 ? 'active' : ''}"></span>
                    </div>
                `;

                item.innerHTML = `
                    <div>
                        <div class="wifi-name">${this.escapeHtml(net.ssid)}</div>
                        <div class="wifi-sec">${net.security} // Ch ${net.channel} // ${net.rate}</div>
                    </div>
                    <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                        <div class="signal-wrapper">
                            ${signalBarsHtml}
                            <span class="wifi-signal-text">${net.signal}%</span>
                        </div>
                        <button class="eva-btn-action" style="padding: 6px 12px; font-size: 11px;">CONECTAR</button>
                    </div>
                `;

                item.addEventListener("click", () => this.promptConnect(net.ssid, net.security !== "Open"));
                this.wifiListContainer.appendChild(item);
            });
        } catch (e) {
            this.wifiListContainer.innerHTML = `<div style='color: var(--magi-red); padding: 12px;'>Error de escaneo: ${e.message}</div>`;
        }
    }

    promptConnect(ssid, isSecure) {
        this.selectedSSID = ssid;
        const promptBox = document.getElementById("wifi-connect-prompt");
        const ssidLabel = document.getElementById("connect-target-ssid");
        const passInput = document.getElementById("wifi-password-input");

        if (promptBox && ssidLabel) {
            ssidLabel.innerText = ssid;
            passInput.value = "";
            promptBox.style.display = "block";

            if (isSecure) {
                passInput.focus();
            }
        }
    }

    cancelConnectionPrompt() {
        const promptBox = document.getElementById("wifi-connect-prompt");
        if (promptBox) {
            promptBox.style.display = "none";
        }
        this.selectedSSID = null;
    }

    async submitConnection() {
        if (!this.selectedSSID) return;

        const passInput = document.getElementById("wifi-password-input");
        const statusMsg = document.getElementById("wifi-connect-status");
        const password = passInput ? passInput.value : "";

        if (statusMsg) {
            statusMsg.style.color = "var(--magi-orange)";
            statusMsg.innerText = "[+] AUTENTICANDO CON " + this.selectedSSID + "...";
        }

        try {
            const res = await fetch("/api/wifi/connect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ssid: this.selectedSSID, password: password })
            });

            const data = await res.json();
            if (data.success) {
                if (statusMsg) {
                    statusMsg.style.color = "var(--magi-green)";
                    statusMsg.innerText = "[OK] CONECTADO EXITOSAMENTE A " + this.selectedSSID;
                }
                setTimeout(() => {
                    this.cancelConnectionPrompt();
                    this.scanWifi();
                    if (window.magiUI) window.magiUI.updateStatus();
                }, 1500);
            } else {
                if (statusMsg) {
                    statusMsg.style.color = "var(--magi-red)";
                    statusMsg.innerText = "[-] ERROR: " + data.message;
                }
            }
        } catch (e) {
            if (statusMsg) {
                statusMsg.style.color = "var(--magi-red)";
                statusMsg.innerText = "[-] ERROR DE ENLACE: " + e.message;
            }
        }
    }

    async scanBluetooth() {
        if (!this.btListContainer) return;
        this.btListContainer.innerHTML = "<div style='color: var(--magi-orange); padding: 12px;'>[+] CONSULTANDO DISPOSITIVOS BLUETOOTH...</div>";

        try {
            const res = await fetch("/api/bluetooth/scan");
            const data = await res.json();

            if (!data.success || !data.devices || data.devices.length === 0) {
                this.btListContainer.innerHTML = "<div style='color: #888; padding: 12px;'>No hay dispositivos Bluetooth vinculados en este momento.</div>";
                return;
            }

            this.btListContainer.innerHTML = "";
            data.devices.forEach(dev => {
                const item = document.createElement("div");
                item.className = "wifi-item";
                item.innerHTML = `
                    <div>
                        <div class="wifi-name">${this.escapeHtml(dev.name)}</div>
                        <div class="wifi-sec">${dev.mac} // ${dev.paired ? "VINCULADO" : "DISPONIBLE"}</div>
                    </div>
                    <button class="eva-btn-action" style="padding: 6px 12px; font-size: 11px;">CONECTAR</button>
                `;
                this.btListContainer.appendChild(item);
            });
        } catch (e) {
            this.btListContainer.innerHTML = `<div style='color: var(--magi-red); padding: 12px;'>Error Bluetooth: ${e.message}</div>`;
        }
    }

    escapeHtml(str) {
        return (str || "").replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.magiNetwork = new MagiNetwork();
});
