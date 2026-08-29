/**
 * MAGI SYSTEM - CORE APPLICATION LOGIC, VOICE I/O & SYSTEMIC DEBATE
 * Evangelion Supercomputer UI Engine (1024x600 Touch Display)
 * Dedicated Core 1 Execution (AntiGravity CLI, Audio Sandboxing, RTOS Supervisor)
 */

class MagiUI {
    constructor() {
        this.activeView = "main";
        this.activeAgentMode = "voice";
        this.isRecording = false;
        this.speechRecognition = null;
        this.debateInterval = null;
        this.debateStartTime = 0;
        this.init();
    }

    init() {
        // Actualización del reloj en tiempo real en la cabecera MAGI
        setInterval(() => {
            const now = new Date();
            const timeStr = now.toTimeString().split(' ')[0] + "." + Math.floor(now.getMilliseconds() / 100);
            const clockEl = document.getElementById("system-live-clock");
            if (clockEl) clockEl.innerText = `TIME: ${timeStr} UTC`;
        }, 100);

        // Pod Clicks -> View Switching
        const podBalthasar = document.getElementById("pod-balthasar");
        const podCasper = document.getElementById("pod-casper");
        const podMelchior = document.getElementById("pod-melchior");

        if (podBalthasar) podBalthasar.addEventListener("click", () => this.switchView("balthasar"));
        if (podCasper) podCasper.addEventListener("click", () => this.switchView("casper"));
        if (podMelchior) podMelchior.addEventListener("click", () => this.switchView("melchior"));

        // Return to MAGI buttons (Layer Minimizing without DOM destruction)
        document.querySelectorAll(".btn-return-magi").forEach(btn => {
            btn.addEventListener("click", () => this.switchView("main"));
        });

        // Balthasar Mode Selector Buttons
        const btnModeVoice = document.getElementById("btn-mode-voice");
        const btnModeText = document.getElementById("btn-mode-text");
        const btnModeTerminal = document.getElementById("btn-mode-terminal");

        if (btnModeVoice) btnModeVoice.addEventListener("click", () => this.switchAgentMode("voice"));
        if (btnModeText) btnModeText.addEventListener("click", () => this.switchAgentMode("text"));
        if (btnModeTerminal) btnModeTerminal.addEventListener("click", () => this.switchAgentMode("terminal"));

        // Push-to-Talk Setup
        this.setupPushToTalk();

        // Prompt Dispatch Buttons
        const btnDispatchVoice = document.getElementById("btn-dispatch-voice-prompt");
        if (btnDispatchVoice) {
            btnDispatchVoice.addEventListener("click", () => {
                const txt = document.getElementById("voice-transcript-output")?.value || "";
                this.dispatchPrompt(txt);
            });
        }

        const btnDispatchText = document.getElementById("btn-dispatch-text-prompt");
        if (btnDispatchText) {
            btnDispatchText.addEventListener("click", () => {
                const txt = document.getElementById("agent-text-input")?.value || "";
                this.dispatchPrompt(txt);
            });
        }

        // Quick Macro Chips
        document.querySelectorAll(".prompt-chip").forEach(chip => {
            chip.addEventListener("click", (e) => {
                const prompt = e.currentTarget.getAttribute("data-prompt");
                const textInput = document.getElementById("agent-text-input");
                if (textInput) {
                    textInput.value = prompt;
                    this.dispatchPrompt(prompt);
                }
            });
        });

        // Test Voice TTS Button
        const btnTestTts = document.getElementById("btn-test-tts");
        if (btnTestTts) {
            btnTestTts.addEventListener("click", () => {
                this.speakMagi("MAGI SYSTEM. BALTHASAR DOS. SUPERCOMPUTADORA INDUSTRIAL HIL EN LINEA.");
            });
        }

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

    /**
     * Non-destructive layer view switcher (<50ms, keeps DOM/iframes alive)
     */
    switchView(viewName) {
        this.activeView = viewName;
        const mainView = document.getElementById("magi-main-view");

        // Ocultar todas las sub-vistas usando clases de opacidad / visibilidad
        document.querySelectorAll(".magi-subview").forEach(sv => {
            sv.classList.remove("active");
        });

        if (viewName === "main") {
            if (mainView) mainView.classList.remove("minimized");
        } else {
            if (mainView) mainView.classList.add("minimized");
            const targetView = document.getElementById(`subview-${viewName}`);
            if (targetView) {
                targetView.classList.add("active");
            }

            // Si es Balthasar, asegurar que el modo activo se inicialice
            if (viewName === "balthasar") {
                this.switchAgentMode(this.activeAgentMode);
            }
        }
    }

    /**
     * Switch Mode in Balthasar Agent Cockpit (Voice / Text / Terminal)
     */
    switchAgentMode(mode) {
        this.activeAgentMode = mode;

        // Actualizar botones de modo
        document.querySelectorAll(".btn-mode").forEach(btn => btn.classList.remove("active"));
        const activeBtn = document.getElementById(`btn-mode-${mode}`);
        if (activeBtn) activeBtn.classList.add("active");

        // Ocultar todos los paneles
        const pVoice = document.getElementById("panel-agent-voice");
        const pText = document.getElementById("panel-agent-text");
        const pTerm = document.getElementById("panel-agent-terminal");

        if (pVoice) pVoice.style.display = (mode === "voice") ? "flex" : "none";
        if (pText) pText.style.display = (mode === "text") ? "flex" : "none";
        if (pTerm) pTerm.style.display = (mode === "terminal") ? "flex" : "none";

        // Si se entra a modo terminal interactiva, asegurar carga única de ttyd
        if (mode === "terminal") {
            const termFrame = document.getElementById("terminal-frame");
            if (termFrame && (!termFrame.src || termFrame.src === "about:blank")) {
                const host = window.location.hostname || "127.0.0.1";
                termFrame.src = `http://${host}:7681/`;
            }
        }
    }

    /**
     * Speech-to-Text (STT) Push-To-Talk Setup
     */
    setupPushToTalk() {
        const btnPtt = document.getElementById("btn-push-to-talk");
        const voiceDot = document.getElementById("voice-indicator");
        const statusText = document.getElementById("voice-status-text");
        const transcriptArea = document.getElementById("voice-transcript-output");

        // Verificar soporte Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.speechRecognition = new SpeechRecognition();
            this.speechRecognition.continuous = true;
            this.speechRecognition.interimResults = true;
            this.speechRecognition.lang = "es-ES";

            this.speechRecognition.onresult = (event) => {
                let interimTranscript = "";
                let finalTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if (transcriptArea) {
                    transcriptArea.value = finalTranscript || interimTranscript;
                }
            };

            this.speechRecognition.onerror = (event) => {
                console.warn("STT Error:", event.error);
                if (statusText) statusText.innerText = "ERROR EN STT: " + event.error.toUpperCase();
            };
        }

        const startRecording = (e) => {
            if (e) e.preventDefault();
            if (this.isRecording) return;
            this.isRecording = true;

            if (btnPtt) btnPtt.classList.add("recording");
            if (voiceDot) {
                voiceDot.classList.remove("ready");
                voiceDot.classList.add("recording");
            }
            if (statusText) statusText.innerText = "RECORDING AUDIO // DICTATE YOUR PROMPT DIRECTIVE...";

            if (this.speechRecognition) {
                try { this.speechRecognition.start(); } catch (err) { /* already started */ }
            }
        };

        const stopRecording = (e) => {
            if (e) e.preventDefault();
            if (!this.isRecording) return;
            this.isRecording = false;

            if (btnPtt) btnPtt.classList.remove("recording");
            if (voiceDot) {
                voiceDot.classList.remove("recording");
                voiceDot.classList.add("ready");
            }
            if (statusText) statusText.innerText = "RECORDING COMPLETED // READY TO EXECUTE PROMPT";

            if (this.speechRecognition) {
                try { this.speechRecognition.stop(); } catch (err) { /* already stopped */ }
            }
        };

        if (btnPtt) {
            // Soporte Touch y Mouse
            btnPtt.addEventListener("pointerdown", startRecording);
            btnPtt.addEventListener("pointerup", stopRecording);
            btnPtt.addEventListener("pointerleave", stopRecording);
            btnPtt.addEventListener("touchstart", startRecording, { passive: false });
            btnPtt.addEventListener("touchend", stopRecording, { passive: false });
        }
    }

    /**
     * Androgynous Accelerated TTS Voice Synthesis (Web Speech API + Backend Fallback)
     */
    speakMagi(text) {
        if (!text) return;

        // 1. Client-Side Chromium Web Speech Synthesis
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Detener locución previa

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "es-ES";
            utterance.rate = 1.6;  // Acelerada (1.5x - 1.75x estilo Evangelion)
            utterance.pitch = 1.25; // Tono andrógino / sintético

            // Buscar voz adecuada si está disponible en Chromium
            const voices = window.speechSynthesis.getVoices();
            const esVoice = voices.find(v => v.lang.startsWith("es") || v.name.toLowerCase().includes("spanish"));
            if (esVoice) utterance.voice = esVoice;

            window.speechSynthesis.speak(utterance);
        }

        // 2. Servidor Backend Core 1 (aplay / espeak-ng) para salida de hardware simultánea
        try {
            fetch("/api/audio/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, rate: 1.6, pitch: 1.25 })
            }).catch(() => {});
        } catch (e) {
            // Silent catch
        }
    }

    /**
     * Dispatch Prompt to AntiGravity Autonomous Agent & Start MAGI Debate
     */
    async dispatchPrompt(promptText) {
        const cleanPrompt = (promptText || "").trim();
        if (!cleanPrompt) {
            alert("Por favor ingrese o dicte una instrucción antes de ejecutar.");
            return;
        }

        // Actualizar consolas
        const consoleVoice = document.getElementById("agent-output-console");
        const consoleText = document.getElementById("agent-text-output-console");
        const stateVoice = document.getElementById("agent-exec-state");
        const stateText = document.getElementById("agent-text-exec-state");

        const msgHeader = `[+] DISPATCHING DIRECTIVE TO ANTIGRAVITY CLI (CORE 1):\n"${cleanPrompt}"\n\n[+] INITIATING MAGI SYSTEMIC TRIPARTITE DELIBERATION...\n`;
        if (consoleVoice) consoleVoice.innerText = msgHeader;
        if (consoleText) consoleText.innerText = msgHeader;

        if (stateVoice) { stateVoice.className = "exec-state-running"; stateVoice.innerText = "DELIBERATING..."; }
        if (stateText) { stateText.className = "exec-state-running"; stateText.innerText = "DELIBERATING..."; }

        // Disparar animación estética de Debate MAGI y locución auditiva
        this.startMagiDebate(cleanPrompt);

        try {
            const res = await fetch("/api/magi/prompt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: cleanPrompt })
            });

            const data = await res.json();
            const outputText = data.output || (data.success ? "Comando ejecutado con exito." : ("Error: " + data.error));

            if (consoleVoice) consoleVoice.innerText = msgHeader + "\n[✓] RESPONSE RECEIVED:\n" + outputText;
            if (consoleText) consoleText.innerText = msgHeader + "\n[✓] RESPONSE RECEIVED:\n" + outputText;

            if (stateVoice) { stateVoice.className = "exec-state-done"; stateVoice.innerText = "CONSENSUS REACHED"; }
            if (stateText) { stateText.className = "exec-state-done"; stateText.innerText = "CONSENSUS REACHED"; }

            // Concluir Debate MAGI
            this.finishMagiDebate(outputText, data.success);

        } catch (e) {
            const errMsg = "Error de enlace con el agente AntiGravity: " + e.message;
            if (consoleVoice) consoleVoice.innerText += "\n[-] " + errMsg;
            if (consoleText) consoleText.innerText += "\n[-] " + errMsg;

            if (stateVoice) { stateVoice.className = "exec-state-idle"; stateVoice.innerText = "FAILED"; }
            if (stateText) { stateText.className = "exec-state-idle"; stateText.innerText = "FAILED"; }

            this.finishMagiDebate(errMsg, false);
        }
    }

    /**
     * MAGI Tripartite Deliberation / Consensus Visualizer Routine
     */
    startMagiDebate(promptText) {
        if (this.debateInterval) clearInterval(this.debateInterval);
        this.debateStartTime = Date.now();

        // 1. Locución auditiva de inicio
        this.speakMagi("MAGI SYSTEM. CONSULTA RECIBIDA. INICIANDO DELIBERACION DE CONSENSO.");

        // 2. Banner central de debate
        const banner = document.getElementById("magi-debate-banner");
        const titleEl = document.getElementById("debate-title-text");
        const verdictEl = document.getElementById("debate-verdict-text");
        const queryFooter = document.getElementById("footer-status-query");

        if (banner) banner.style.display = "block";
        if (titleEl) titleEl.innerText = "DELIBERATING // SYNCHRONIZING";
        if (verdictEl) verdictEl.innerText = "PODS 1, 2, 3 COUPLING TO REALTIME BUS...";
        if (queryFooter) queryFooter.innerText = "QUERY: " + promptText.toUpperCase();

        // 3. Activar animación en los 3 pods
        const pods = [
            { id: "pod-balthasar", badge: "pod-status-balthasar", fill: "progress-fill-balthasar", name: "BALTHASAR-2" },
            { id: "pod-casper", badge: "pod-status-casper", fill: "progress-fill-casper", name: "CASPER-3" },
            { id: "pod-melchior", badge: "pod-status-melchior", fill: "progress-fill-melchior", name: "MELCHIOR-1" }
        ];

        pods.forEach(p => {
            const podEl = document.getElementById(p.id);
            if (podEl) {
                podEl.classList.remove("consensus");
                podEl.classList.add("debating");
            }
        });

        // 4. Bucle dinámico de deliberación (simulación estética de porcentaje y sincronización)
        this.debateInterval = setInterval(() => {
            const elapsed = (Date.now() - this.debateStartTime) / 1000;
            const syncProgress = Math.min(96, Math.floor(elapsed * 25 + Math.random() * 10));

            const bar = document.getElementById("debate-sync-progress");
            if (bar) bar.style.width = syncProgress + "%";

            // Progreso individual de cada pod con micro-variaciones
            const p1 = Math.min(99, Math.floor(syncProgress + (Math.sin(elapsed * 3) * 5)));
            const p2 = Math.min(99, Math.floor(syncProgress + (Math.cos(elapsed * 4) * 4)));
            const p3 = Math.min(99, Math.floor(syncProgress + (Math.sin(elapsed * 2) * 6)));

            const fMelchior = document.getElementById("progress-fill-melchior");
            const fBalthasar = document.getElementById("progress-fill-balthasar");
            const fCasper = document.getElementById("progress-fill-casper");

            if (fMelchior) fMelchior.style.width = p1 + "%";
            if (fBalthasar) fBalthasar.style.width = p2 + "%";
            if (fCasper) fCasper.style.width = p3 + "%";

            const bMelchior = document.getElementById("pod-status-melchior");
            const bBalthasar = document.getElementById("pod-status-balthasar");
            const bCasper = document.getElementById("pod-status-casper");

            if (bMelchior) bMelchior.innerText = `DELIBERATING: ${p1}%`;
            if (bBalthasar) bBalthasar.innerText = `PROCESSING: ${p2}%`;
            if (bCasper) bCasper.innerText = `SIMULATING: ${p3}%`;
        }, 120);
    }

    /**
     * Finish MAGI Debate & Announce Tripartite Consensus
     */
    finishMagiDebate(resultText, isSuccess) {
        if (this.debateInterval) {
            clearInterval(this.debateInterval);
            this.debateInterval = null;
        }

        const banner = document.getElementById("magi-debate-banner");
        const titleEl = document.getElementById("debate-title-text");
        const verdictEl = document.getElementById("debate-verdict-text");
        const bar = document.getElementById("debate-sync-progress");

        if (bar) bar.style.width = "100%";
        if (titleEl) {
            titleEl.innerText = isSuccess ? "CONSENSO ALCANZADO" : "CONSENSO CONDICIONAL";
            titleEl.style.color = isSuccess ? "var(--magi-green)" : "var(--magi-orange)";
        }
        if (verdictEl) {
            verdictEl.innerText = isSuccess ? "DECISION APROBADA (3/3 PODS // 100% ACUERDO)" : "EJECUCION FINALIZADA CON AVISOS";
        }

        // Pods a estado de consenso verde
        ["pod-balthasar", "pod-casper", "pod-melchior"].forEach(id => {
            const podEl = document.getElementById(id);
            if (podEl) {
                podEl.classList.remove("debating");
                podEl.classList.add("consensus");
            }
        });

        const bMelchior = document.getElementById("pod-status-melchior");
        const bBalthasar = document.getElementById("pod-status-balthasar");
        const bCasper = document.getElementById("pod-status-casper");

        if (bMelchior) bMelchior.innerText = "AGREED // 100%";
        if (bBalthasar) bBalthasar.innerText = "CONSENSUS // 100%";
        if (bCasper) bCasper.innerText = "VERIFIED // 100%";

        // Locución auditiva de conclusión
        this.speakMagi("MAGI SYSTEM. CONSENSO ALCANZADO. TAREA COMPLETADA.");

        // Restaurar estado visual tras 6 segundos
        setTimeout(() => {
            if (banner) banner.style.display = "none";
            ["pod-balthasar", "pod-casper", "pod-melchior"].forEach(id => {
                const podEl = document.getElementById(id);
                if (podEl) {
                    podEl.classList.remove("consensus");
                    podEl.classList.remove("debating");
                }
            });

            if (bMelchior) bMelchior.innerText = "STANDBY";
            if (bBalthasar) bBalthasar.innerText = "STANDBY";
            if (bCasper) bCasper.innerText = "STANDBY";

            const fMelchior = document.getElementById("progress-fill-melchior");
            const fBalthasar = document.getElementById("progress-fill-balthasar");
            const fCasper = document.getElementById("progress-fill-casper");

            if (fMelchior) fMelchior.style.width = "0%";
            if (fBalthasar) fBalthasar.style.width = "0%";
            if (fCasper) fCasper.style.width = "0%";
        }, 6000);
    }

    /**
     * Periodic Status & Telemetry Fetch
     */
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
            if (wifiEl) wifiEl.innerText = data.wifi_connected ? data.wifi_ssid : "ETH0 DIRECT LINK";
            if (ipEl) ipEl.innerText = data.ip_address;
            if (rtEl) {
                rtEl.innerText = data.rt_alive ? "CORE 3 RT ALIVE" : "ACTIVE / CORE 3";
                rtEl.style.color = data.rt_alive ? "var(--magi-green)" : "var(--magi-orange)";
            }

            // Melchior Telemetry Cards
            const telemSpeed = document.getElementById("telem-speed");
            if (telemSpeed) {
                const rndSpeed = (Math.sin(Date.now() / 1000) * 15 + 150).toFixed(1);
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
