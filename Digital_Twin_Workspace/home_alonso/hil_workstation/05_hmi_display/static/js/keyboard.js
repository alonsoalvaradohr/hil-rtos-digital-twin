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
        this.init();
    }

    init() {
        if (!this.container) return;

        // Escuchar foco en inputs
        document.addEventListener("focusin", (e) => {
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
                this.activeInput = e.target;
                this.show();
            }
        });

        this.render();
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

        const layout = this.isShift ? shiftLayout : defaultLayout;

        this.container.innerHTML = "";

        layout.forEach(row => {
            const rowEl = document.createElement("div");
            rowEl.className = "kb-row";

            row.forEach(key => {
                const keyEl = document.createElement("div");
                keyEl.className = "kb-key";
                keyEl.innerText = key;

                if (key === "SPACE") keyEl.classList.add("kb-key-space");
                if (key === "SHIFT" || key === "BKSP" || key === "?123" || key === "HIDE") keyEl.classList.add("kb-key-wide");
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
            this.isShift = !this.isShift;
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
