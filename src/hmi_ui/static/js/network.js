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
        this.requestTimeoutMs = 25000;
        this.wifiScanController = null;
        this.bluetoothScanController = null;
        this.wifiScanSequence = 0;
        this.bluetoothScanSequence = 0;
        this.knownWifiController = null;
        this.wifiReconnectPending = false;
        this.bluetoothActionPending = new Set();
        this.bluetoothActionControllers = new Map();
        this.knownWifiContainer = null;
        this.init();
    }

    async fetchJson(url, options = {}, timeoutMs = this.requestTimeoutMs, externalSignal = null) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort("timeout"), timeoutMs);
        const abortForwarder = () => controller.abort("superseded");
        if (externalSignal) {
            if (externalSignal.aborted) controller.abort("superseded");
            else externalSignal.addEventListener("abort", abortForwarder, { once: true });
        }
        try {
            const response = await fetch(url, { ...options, signal: controller.signal });
            let data;
            try {
                data = await response.json();
            } catch (error) {
                throw new Error(`HTTP ${response.status}: respuesta JSON invalida`);
            }
            if (!response.ok || !data.success) {
                const literalError = data.error || data.message || `HTTP ${response.status}`;
                const error = new Error(literalError);
                error.status = response.status;
                error.data = data;
                throw error;
            }
            return data;
        } catch (error) {
            if (controller.signal.aborted) {
                const reason = controller.signal.reason === "superseded" ? "Solicitud reemplazada" : "Tiempo de espera agotado";
                throw new DOMException(reason, "AbortError");
            }
            throw error;
        } finally {
            clearTimeout(timer);
            if (externalSignal) externalSignal.removeEventListener("abort", abortForwarder);
        }
    }

    init() {
        const bindTap = (el, handler) => {
            if (!el) return;
            let touchHandled = false;
            el.addEventListener("pointerdown", () => {
                el.style.opacity = "0.75";
            });
            el.addEventListener("pointerup", (e) => {
                el.style.opacity = "";
                touchHandled = true;
                setTimeout(() => { touchHandled = false; }, 400);
                handler(e);
            });
            el.addEventListener("click", (e) => {
                el.style.opacity = "";
                if (touchHandled) return;
                handler(e);
            });
        };

        const btnNet = document.getElementById("btn-open-network");
        bindTap(btnNet, () => this.open());

        const btnClose = document.getElementById("btn-close-network");
        bindTap(btnClose, () => this.close());

        const tabWifi = document.getElementById("tab-btn-wifi");
        const tabBt = document.getElementById("tab-btn-bt");

        bindTap(tabWifi, () => this.switchTab("wifi"));
        bindTap(tabBt, () => this.switchTab("bluetooth"));

        const btnScanWifi = document.getElementById("btn-rescan-wifi");
        bindTap(btnScanWifi, () => this.scanWifi());

        const btnConfirmConn = document.getElementById("btn-confirm-connect");
        bindTap(btnConfirmConn, () => this.submitConnection());

        const btnCancelConn = document.getElementById("btn-cancel-connect");
        bindTap(btnCancelConn, () => this.cancelConnectionPrompt());
        this.setupKnownWifiControls();
    }

    setupKnownWifiControls() {
        if (!this.wifiListContainer || this.knownWifiContainer) return;
        const section = document.createElement("section");
        section.setAttribute("aria-label", "Perfiles Wi-Fi conocidos");
        section.style.cssText = "border-top:1px solid var(--magi-orange); padding:8px;";
        const button = document.createElement("button");
        button.type = "button";
        button.className = "eva-btn-action";
        button.textContent = "RECONECTAR CONOCIDA";
        button.addEventListener("click", () => this.reconnectKnownWifi(button));
        const status = document.createElement("div");
        status.className = "known-wifi-status";
        status.setAttribute("role", "status");
        status.setAttribute("aria-live", "polite");
        const list = document.createElement("div");
        list.className = "known-wifi-list";
        section.append(button, status, list);
        this.wifiListContainer.insertAdjacentElement("afterend", section);
        this.knownWifiContainer = section;
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
        if (this.wifiScanController) this.wifiScanController.abort();
        if (this.bluetoothScanController) this.bluetoothScanController.abort();
        if (this.knownWifiController) this.knownWifiController.abort();
        this.bluetoothActionControllers.forEach(controller => controller.abort());
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
        if (this.wifiScanController) this.wifiScanController.abort();
        const controller = new AbortController();
        const sequence = ++this.wifiScanSequence;
        this.wifiScanController = controller;
        this.wifiListContainer.innerHTML = "<div style='color: var(--magi-orange); padding: 12px;'>[+] ESCANEANDO ESPECTRO DE RADIO WI-FI...</div>";
        this.loadKnownWifi();

        try {
            const data = await this.fetchJson("/api/wifi/scan", {}, this.requestTimeoutMs, controller.signal);
            if (sequence !== this.wifiScanSequence) return;

            if (!Array.isArray(data.networks) || data.networks.length === 0) {
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

                let lastItemTap = 0;
                const onConnectClick = (e) => {
                    const now = Date.now();
                    if (now - lastItemTap < 250) return;
                    lastItemTap = now;
                    this.promptConnect(net.ssid, net.security !== "Open");
                };
                item.addEventListener("pointerup", onConnectClick);
                item.addEventListener("click", onConnectClick);
                this.wifiListContainer.appendChild(item);
            });
        } catch (e) {
            if (sequence !== this.wifiScanSequence || (e.name === "AbortError" && controller.signal.aborted)) return;
            this.wifiListContainer.innerHTML = `<div style='color: var(--magi-red); padding: 12px;'>Error de escaneo: ${e.message}</div>`;
        } finally {
            if (sequence === this.wifiScanSequence) this.wifiScanController = null;
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
            if (passInput) passInput.disabled = true;
            const data = await this.fetchJson("/api/wifi/connect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ssid: this.selectedSSID, password: password })
            }, this.requestTimeoutMs);
            if (data.autoconnect_verified !== true) {
                const error = new Error("Enlace recibido sin autoconnect verificado");
                error.data = data;
                throw error;
            }
            if (statusMsg) {
                statusMsg.style.color = "var(--magi-green)";
                statusMsg.innerText = "[OK] " + (data.message || `CONECTADO A ${this.selectedSSID}`);
            }
            setTimeout(() => {
                this.cancelConnectionPrompt();
                this.scanWifi();
                if (window.magiUI) window.magiUI.updateStatus();
            }, 1500);
        } catch (e) {
            if (statusMsg) {
                statusMsg.style.color = "var(--magi-red)";
                statusMsg.innerText = "[-] ERROR DE ENLACE: " + e.message;
            }
        } finally {
            if (passInput) passInput.disabled = false;
        }
    }

    async loadKnownWifi() {
        if (!this.knownWifiContainer) return;
        if (this.knownWifiController) this.knownWifiController.abort();
        const controller = new AbortController();
        this.knownWifiController = controller;
        const list = this.knownWifiContainer.querySelector(".known-wifi-list");
        const status = this.knownWifiContainer.querySelector(".known-wifi-status");
        status.textContent = "[+] CARGANDO PERFILES CONOCIDOS...";
        try {
            const data = await this.fetchJson("/api/wifi/known", {}, this.requestTimeoutMs, controller.signal);
            list.innerHTML = "";
            (data.profiles || []).forEach(profile => {
                const row = document.createElement("div");
                row.className = "wifi-sec";
                row.textContent = `${profile.name} // SSID: ${profile.ssid} // AUTOCONNECT: ${profile.autoconnect ? "SI" : "NO"} // PRIORIDAD: ${profile.priority}`;
                list.appendChild(row);
            });
            status.textContent = data.profiles?.length ? "PERFILES CONOCIDOS VERIFICADOS" : "NO HAY PERFILES CONOCIDOS";
        } catch (error) {
            if (error.name === "AbortError" && controller.signal.aborted) return;
            status.textContent = `ERROR PERFILES: ${error.message}`;
        } finally {
            if (this.knownWifiController === controller) this.knownWifiController = null;
        }
    }

    async reconnectKnownWifi(button) {
        if (this.wifiReconnectPending) return;
        this.wifiReconnectPending = true;
        const status = this.knownWifiContainer.querySelector(".known-wifi-status");
        button.disabled = true;
        status.textContent = "[+] RECONECTANDO PERFIL CONOCIDO...";
        try {
            const data = await this.fetchJson("/api/wifi/reconnect", {
                method: "POST", headers: { "Content-Type": "application/json" }, body: "{}"
            }, this.requestTimeoutMs);
            if (data.verified !== true) throw new Error("El backend no verifico el UUID reconectado");
            status.textContent = `[OK] UUID VERIFICADO: ${data.uuid}`;
            await this.loadKnownWifi();
            this.scanWifi();
        } catch (error) {
            status.textContent = `[-] RECONEXION FALLIDA: ${error.message}`;
        } finally {
            button.disabled = false;
            this.wifiReconnectPending = false;
        }
    }

    async scanBluetooth() {
        if (!this.btListContainer) return;
        if (this.bluetoothScanController) this.bluetoothScanController.abort();
        const controller = new AbortController();
        const sequence = ++this.bluetoothScanSequence;
        this.bluetoothScanController = controller;
        this.btListContainer.innerHTML = "<div style='color: var(--magi-orange); padding: 12px;'>[+] CONSULTANDO DISPOSITIVOS BLUETOOTH...</div>";

        try {
            const data = await this.fetchJson("/api/bluetooth/scan", {}, 30000, controller.signal);
            if (sequence !== this.bluetoothScanSequence) return;

            if (!Array.isArray(data.devices) || data.devices.length === 0) {
                this.btListContainer.innerHTML = "<div style='color: #888; padding: 12px;'>Escaneo completado: no se detectaron dispositivos Bluetooth.</div>";
                return;
            }

            this.btListContainer.innerHTML = "";
            data.devices.forEach(dev => {
                const item = document.createElement("div");
                item.className = "wifi-item";
                const state = [dev.paired ? "VINCULADO" : "NO VINCULADO", dev.trusted ? "CONFIABLE" : "NO CONFIABLE", dev.connected ? "CONECTADO" : "DESCONECTADO"].join(" // ");
                const actions = [];
                if (!dev.paired) actions.push(["pair", "EMPAREJAR"]);
                if (dev.paired && !dev.trusted) actions.push(["trust", "CONFIAR"]);
                actions.push(dev.connected ? ["disconnect", "DESCONECTAR"] : ["connect", "CONECTAR"]);
                item.innerHTML = `
                    <div>
                        <div class="wifi-name">${this.escapeHtml(dev.name)}</div>
                        <div class="wifi-sec">${this.escapeHtml(dev.mac)} // ${state}</div>
                        <div class="bt-action-status" style="color: var(--magi-orange); font-size: 11px;"></div>
                    </div>
                    <div class="bt-actions"></div>
                `;
                const actionContainer = item.querySelector(".bt-actions");
                actions.forEach(([action, label]) => {
                    const button = document.createElement("button");
                    button.className = "eva-btn-action";
                    button.style.cssText = "padding: 6px 12px; font-size: 11px; margin-left: 6px;";
                    button.textContent = label;
                    button.addEventListener("click", () => this.bluetoothAction(dev.mac, action, item));
                    actionContainer.appendChild(button);
                });
                this.btListContainer.appendChild(item);
            });
        } catch (e) {
            if (sequence !== this.bluetoothScanSequence || (e.name === "AbortError" && controller.signal.aborted)) return;
            this.btListContainer.innerHTML = `<div style='color: var(--magi-red); padding: 12px;'>Error Bluetooth: ${e.message}</div>`;
        } finally {
            if (sequence === this.bluetoothScanSequence) this.bluetoothScanController = null;
        }
    }

    renderPairingChallenge(mac, item, data) {
        const previous = item.querySelector(".bt-pairing-challenge");
        if (previous) previous.remove();
        const panel = document.createElement("div");
        panel.className = "bt-pairing-challenge";
        panel.setAttribute("role", "group");
        panel.setAttribute("aria-label", "Desafio de emparejamiento Bluetooth");
        panel.style.cssText = "width:100%; padding:8px; border:1px solid var(--magi-orange);";
        const label = document.createElement("div");
        label.textContent = data.passkey_display
            ? `${data.challenge_type}: ${data.passkey_display}`
            : `BlueZ solicita ${data.challenge_type || "respuesta de pairing"}`;
        panel.appendChild(label);
        if (["pin", "passkey"].includes(data.challenge_type)) {
            const input = document.createElement("input");
            input.type = "text";
            input.inputMode = "numeric";
            input.pattern = "[0-9]{1,6}";
            input.maxLength = 6;
            input.setAttribute("aria-label", "PIN o passkey Bluetooth");
            const submit = document.createElement("button");
            submit.type = "button";
            submit.className = "eva-btn-action";
            submit.textContent = "ENVIAR PIN";
            submit.addEventListener("click", () => {
                if (!/^[0-9]{1,6}$/.test(input.value)) {
                    label.textContent = "PIN invalido: use de 1 a 6 digitos";
                    return;
                }
                this.bluetoothAction(mac, "pair", item, { passkey: input.value });
            });
            panel.append(input, submit);
        } else if (data.challenge_type === "confirmation") {
            const yes = document.createElement("button");
            yes.type = "button";
            yes.className = "eva-btn-action";
            yes.textContent = "SI, COINCIDE";
            yes.addEventListener("click", () => this.bluetoothAction(mac, "pair", item, { confirm: true }));
            const no = document.createElement("button");
            no.type = "button";
            no.className = "eva-btn-action";
            no.textContent = "NO, RECHAZAR";
            no.addEventListener("click", () => this.bluetoothAction(mac, "pair", item, { confirm: false }));
            panel.append(yes, no);
        }
        item.appendChild(panel);
    }

    async bluetoothAction(mac, action, item, pairingResponse = {}) {
        if (this.bluetoothActionPending.has(mac)) return;
        this.bluetoothActionPending.add(mac);
        const controller = new AbortController();
        this.bluetoothActionControllers.set(mac, controller);
        const status = item.querySelector(".bt-action-status");
        const buttons = Array.from(item.querySelectorAll("button"));
        let pairingChallenge = false;
        buttons.forEach(button => { button.disabled = true; });
        status.style.color = "var(--magi-orange)";
        status.textContent = `[+] ${action.toUpperCase()} EN PROGRESO...`;
        try {
            const data = await this.fetchJson(`/api/bluetooth/${action}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mac, ...pairingResponse })
            }, 30000, controller.signal);
            if (!data.verified) throw new Error("El backend no verifico el estado Bluetooth solicitado");
            status.style.color = "var(--magi-green)";
            status.textContent = `[OK] ${action.toUpperCase()} VERIFICADO`;
            setTimeout(() => this.scanBluetooth(), 500);
        } catch (error) {
            if (error.data?.pairing_required) {
                pairingChallenge = true;
                status.style.color = "var(--magi-orange)";
                status.textContent = `[+] RESPUESTA REQUERIDA${error.data.error_code ? ` // ${error.data.error_code}` : ""}`;
                this.renderPairingChallenge(mac, item, error.data);
                return;
            }
            status.style.color = "var(--magi-red)";
            status.textContent = `[-] ${error.data?.error_code ? `${error.data.error_code}: ` : ""}${error.message}`;
        } finally {
            this.bluetoothActionPending.delete(mac);
            this.bluetoothActionControllers.delete(mac);
            if (!pairingChallenge) buttons.forEach(button => { button.disabled = false; });
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
