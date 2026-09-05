/**
 * MAGI SYSTEM - TACTICAL ON-SCREEN KEYBOARD (OSK)
 * Touch-optimized for 7-inch display (1024x600)
 */

class MagiKeyboard {
    constructor() {
        this.activeInput = null;
        this.isShift = false;
        this.isSymbol = false;
        this.container = document.getElementById("magi-virtual-keyboard");
        this.terminalOskRequestPending = false;
        this.terminalOskDesired = false;
        this.terminalActivationLayer = null;
        this.terminalHideButton = null;
        this.terminalStatus = null;
        this.init();
    }

    init() {
        if (this.container) {
            // Escuchar foco en inputs
            document.addEventListener("focusin", (e) => {
                if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
                    this.activeInput = e.target;
                    this.show();
                }
            });

            this.render();
        }
        this.setupTerminalKeyboard();
    }

    async terminalOskRequest(action) {
        if (this.terminalOskRequestPending) {
            throw new Error("Ya existe una solicitud OSK en curso");
        }
        this.terminalOskRequestPending = true;
        try {
            const response = await fetch(`/api/osk/${action}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            let data;
            try {
                data = await response.json();
            } catch (error) {
                throw new Error(`HTTP ${response.status}: respuesta JSON invalida`);
            }
            if (!response.ok || data.success !== true) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            return data;
        } finally {
            this.terminalOskRequestPending = false;
        }
    }

    setupTerminalKeyboard() {
        const panel = document.getElementById("panel-agent-terminal");
        const frame = document.getElementById("terminal-frame");
        if (!panel || !frame) return;

        panel.style.position = "relative";

        const activationLayer = document.createElement("button");
        activationLayer.type = "button";
        activationLayer.setAttribute("aria-label", "Activar teclado para la terminal");
        activationLayer.textContent = "TOCAR PARA ACTIVAR TERMINAL Y TECLADO";
        activationLayer.style.cssText = [
            "position:absolute", "inset:0", "z-index:20", "border:1px solid var(--magi-orange)",
            "background:rgba(0,0,0,0.35)", "color:var(--magi-orange)", "font:inherit",
            "cursor:pointer", "touch-action:manipulation"
        ].join(";");

        const hideButton = document.createElement("button");
        hideButton.type = "button";
        hideButton.className = "eva-btn-action";
        hideButton.setAttribute("aria-label", "Ocultar teclado de la terminal");
        hideButton.textContent = "OCULTAR TECLADO";
        hideButton.style.cssText = "display:none; position:absolute; top:6px; right:6px; z-index:30; padding:6px 10px;";

        const status = document.createElement("div");
        status.setAttribute("role", "status");
        status.setAttribute("aria-live", "polite");
        status.style.cssText = "display:none; position:absolute; left:8px; bottom:8px; z-index:31; padding:6px; background:#080808; color:var(--magi-red);";

        panel.append(activationLayer, hideButton, status);
        this.terminalActivationLayer = activationLayer;
        this.terminalHideButton = hideButton;
        this.terminalStatus = status;

        activationLayer.addEventListener("pointerdown", async (event) => {
            event.preventDefault();
            if (this.terminalOskRequestPending) return;
            this.terminalOskDesired = true;
            activationLayer.disabled = true;
            activationLayer.textContent = "ACTIVANDO TECLADO...";
            status.style.display = "none";
            try {
                await this.terminalOskRequest("show");
                if (!this.terminalOskDesired) {
                    await this.hideTerminalKeyboard();
                    return;
                }
                activationLayer.style.display = "none";
                hideButton.style.display = "block";
                frame.focus();
            } catch (error) {
                this.terminalOskDesired = false;
                activationLayer.disabled = false;
                activationLayer.textContent = "REINTENTAR ACTIVACION DE TERMINAL Y TECLADO";
                status.textContent = `ERROR OSK: ${error.message}`;
                status.style.display = "block";
            }
        });

        hideButton.addEventListener("click", () => this.hideTerminalKeyboard());

        const observer = new MutationObserver(() => {
            if (panel.style.display === "none") this.hideTerminalKeyboard();
            else this.reactivateTerminalLayer();
        });
        observer.observe(panel, { attributes: true, attributeFilter: ["style", "class"] });
    }

    reactivateTerminalLayer() {
        if (!this.terminalActivationLayer || this.terminalOskDesired) return;
        this.terminalActivationLayer.disabled = false;
        this.terminalActivationLayer.textContent = "TOCAR PARA ACTIVAR TERMINAL Y TECLADO";
        this.terminalActivationLayer.style.display = "block";
        if (this.terminalHideButton) this.terminalHideButton.style.display = "none";
    }

    async hideTerminalKeyboard() {
        this.terminalOskDesired = false;
        if (this.terminalOskRequestPending) return;
        if (this.terminalHideButton) this.terminalHideButton.disabled = true;
        try {
            await this.terminalOskRequest("hide");
            if (this.terminalStatus) this.terminalStatus.style.display = "none";
        } catch (error) {
            if (this.terminalStatus) {
                this.terminalStatus.textContent = `ERROR AL OCULTAR OSK: ${error.message}`;
                this.terminalStatus.style.display = "block";
            }
        } finally {
            if (this.terminalHideButton) this.terminalHideButton.disabled = false;
            this.reactivateTerminalLayer();
        }
    }

    show() {
        if (this.container) {
            this.container.style.display = "flex";
        }
    }

    hide() {
        if (this.container) {
            this.container.style.display = "none";
        }
        if (this.activeInput) {
            this.activeInput.blur();
            this.activeInput = null;
        }
    }

    render() {
        if (!this.container) return;

        const defaultLayout = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'"],
            ["SHIFT", "z", "x", "c", "v", "b", "n", "m", ",", ".", "BKSP"],
            ["?123", "SPACE", "ENTER", "HIDE"]
        ];

        const shiftLayout = [
            ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "{", "}"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ":", "\""],
            ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", "<", ">", "BKSP"],
            ["?123", "SPACE", "ENTER", "HIDE"]
        ];

        const symbolLayout = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
            ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+"],
            ["?", "/", "\\", "|", "<", ">", "[", "]", "{", "}", ";", ":"],
            ["ABC", "'", "\"", ",", ".", "`", "~", "BKSP"],
            ["SPACE", "ENTER", "HIDE"]
        ];

        const layout = this.isSymbol ? symbolLayout : (this.isShift ? shiftLayout : defaultLayout);

        this.container.innerHTML = "";

        layout.forEach(row => {
            const rowEl = document.createElement("div");
            rowEl.className = "kb-row";

            row.forEach(key => {
                const keyEl = document.createElement("div");
                keyEl.className = "kb-key";
                keyEl.innerText = key;

                if (key === "SPACE") keyEl.classList.add("kb-key-space");
                if (key === "SHIFT" || key === "BKSP" || key === "?123" || key === "ABC" || key === "HIDE") keyEl.classList.add("kb-key-wide");
                if (key === "ENTER") keyEl.classList.add("kb-key-enter", "kb-key-wide");

                keyEl.addEventListener("pointerdown", (e) => {
                    e.preventDefault();
                    this.handleKey(key);
                });

                rowEl.appendChild(keyEl);
            });

            this.container.appendChild(rowEl);
        });
    }

    handleKey(key) {
        if (!this.activeInput) return;

        if (key === "SHIFT") {
            this.isShift = !this.isShift;
            this.render();
            return;
        }

        if (key === "?123") {
            this.isSymbol = true;
            this.isShift = false;
            this.render();
            return;
        }

        if (key === "ABC") {
            this.isSymbol = false;
            this.render();
            return;
        }

        if (key === "HIDE") {
            this.hide();
            return;
        }

        if (key === "ENTER") {
            const enterEvent = new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13 });
            this.activeInput.dispatchEvent(enterEvent);
            this.hide();
            return;
        }

        if (key === "BKSP") {
            const val = this.activeInput.value;
            this.activeInput.value = val.slice(0, -1);
            this.activeInput.dispatchEvent(new Event("input", { bubbles: true }));
            return;
        }

        const char = (key === "SPACE") ? " " : key;
        this.activeInput.value += char;
        this.activeInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.magiKeyboard = new MagiKeyboard();
});
