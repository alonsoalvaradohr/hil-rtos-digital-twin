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
        this.finalTranscript = "";
        this.shouldRestartRecognition = false;
        this.recognitionStarting = false;
        this.microphoneAccessVerified = false;
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

        // Helper para respuesta táctil y de puntero instantánea sin tap-delay ni doble disparo
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

        // Pod Clicks / Touch -> View Switching
        const podBalthasar = document.getElementById("pod-balthasar");
        const podCasper = document.getElementById("pod-casper");
        const podMelchior = document.getElementById("pod-melchior");

        bindTap(podBalthasar, () => this.switchView("balthasar"));
        bindTap(podCasper, () => this.switchView("casper"));
        bindTap(podMelchior, () => this.switchView("melchior"));

        // Return to MAGI buttons (Layer Minimizing without DOM destruction)
        document.querySelectorAll(".btn-return-magi").forEach(btn => {
            bindTap(btn, () => this.switchView("main"));
        });

        // Balthasar Mode Selector Buttons
        const btnModeVoice = document.getElementById("btn-mode-voice");
        const btnModeText = document.getElementById("btn-mode-text");
        const btnModeTerminal = document.getElementById("btn-mode-terminal");

        bindTap(btnModeVoice, () => this.switchAgentMode("voice"));
        bindTap(btnModeText, () => this.switchAgentMode("text"));
        bindTap(btnModeTerminal, () => this.switchAgentMode("terminal"));

        // Push-to-Talk Setup
        this.setupPushToTalk();

        // Prompt Dispatch Buttons
        const btnDispatchVoice = document.getElementById("btn-dispatch-voice-prompt");
        if (btnDispatchVoice) {
            bindTap(btnDispatchVoice, () => {
                const txt = document.getElementById("voice-transcript-output")?.value || "";
                this.dispatchPrompt(txt);
            });
        }

        const btnDispatchText = document.getElementById("btn-dispatch-text-prompt");
        if (btnDispatchText) {
            bindTap(btnDispatchText, () => {
                const txt = document.getElementById("agent-text-input")?.value || "";
                this.dispatchPrompt(txt);
            });
        }

        // Quick Macro Chips
        document.querySelectorAll(".prompt-chip").forEach(chip => {
            bindTap(chip, (e) => {
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
            bindTap(btnTestTts, () => {
                this.speakMagi("MAGI SYSTEM. BALTHASAR DOS. SUPERCOMPUTADORA INDUSTRIAL HIL EN LINEA.");
            });
        }

        // Motor Control Buttons in Casper View
        const btnMotorEnable = document.getElementById("btn-motor-enable");
        const btnMotorStop = document.getElementById("btn-motor-stop");
        const btnMotorEstop = document.getElementById("btn-motor-estop");
        const speedSlider = document.getElementById("speed-slider");

        if (btnMotorEnable) {
            bindTap(btnMotorEnable, () => {
                const spd = speedSlider ? parseFloat(speedSlider.value) : 100.0;
                this.sendHilCommand(1, spd, 1);
            });
        }

        if (btnMotorStop) {
            bindTap(btnMotorStop, () => {
                this.sendHilCommand(1, 0.0, 1);
            });
        }

        if (btnMotorEstop) {
            bindTap(btnMotorEstop, () => {
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

        const setVoiceState = (message, state = "ready") => {
            if (statusText) statusText.innerText = message;
            if (btnPtt) btnPtt.classList.toggle("recording", state === "recording");
            if (voiceDot) {
                voiceDot.classList.toggle("recording", state === "recording");
                voiceDot.classList.toggle("ready", state !== "recording");
            }
        };

        const diagnoseMicrophone = async () => {
            if (this.microphoneAccessVerified) return true;
            if (!window.isSecureContext) {
                setVoiceState("STT NO SEGURO: Chromium requiere HTTPS o localhost para habilitar microfono", "error");
                return false;
            }
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                setVoiceState("STT NO DISPONIBLE: getUserMedia no existe en este navegador", "error");
                return false;
            }
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());
                this.microphoneAccessVerified = true;
                return true;
            } catch (error) {
                setVoiceState(`ERROR DE MICROFONO: ${error.name}: ${error.message}`, "error");
                return false;
            }
        };

        // Verificar soporte Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.speechRecognition = new SpeechRecognition();
            this.speechRecognition.continuous = true;
            this.speechRecognition.interimResults = true;
            this.speechRecognition.lang = "es-ES";

            this.speechRecognition.onresult = (event) => {
                let interimTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        const fragment = event.results[i][0].transcript.trim();
                        if (fragment) this.finalTranscript = `${this.finalTranscript} ${fragment}`.trim();
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if (transcriptArea) {
                    transcriptArea.value = `${this.finalTranscript} ${interimTranscript}`.trim();
                }
            };

            this.speechRecognition.onerror = (event) => {
                console.warn("STT Error:", event.error);
                this.recognitionStarting = false;
                if (["not-allowed", "service-not-allowed", "audio-capture"].includes(event.error)) {
                    this.shouldRestartRecognition = false;
                    this.isRecording = false;
                }
                setVoiceState(`ERROR EN STT: ${event.error.toUpperCase()}${event.message ? `: ${event.message}` : ""}`, "error");
            };
            this.speechRecognition.onstart = () => {
                this.recognitionStarting = false;
                this.isRecording = true;
                setVoiceState("GRABACION CONTINUA ACTIVA // PAUSE PARA DETENER", "recording");
            };
            this.speechRecognition.onend = () => {
                this.recognitionStarting = false;
                this.isRecording = false;
                if (this.shouldRestartRecognition) {
                    window.setTimeout(() => startRecording(), 250);
                } else {
                    setVoiceState("STT PAUSADO // LISTO PARA REANUDAR O EJECUTAR", "ready");
                }
            };
        } else {
            setVoiceState("STT NO SOPORTADO POR ESTE NAVEGADOR", "error");
        }

        const startRecording = async (e) => {
            if (e) e.preventDefault();
            if (!this.speechRecognition || this.isRecording || this.recognitionStarting) return;
            if (!(await diagnoseMicrophone())) return;
            this.shouldRestartRecognition = true;
            this.recognitionStarting = true;
            setVoiceState("INICIANDO MICROFONO...", "recording");
            try {
                this.speechRecognition.start();
            } catch (error) {
                this.recognitionStarting = false;
                this.shouldRestartRecognition = false;
                setVoiceState(`NO SE PUDO INICIAR STT: ${error.name}: ${error.message}`, "error");
            }
        };

        const stopRecording = (e) => {
            if (e) e.preventDefault();
            this.shouldRestartRecognition = false;
            if (!this.speechRecognition || (!this.isRecording && !this.recognitionStarting)) return;
            try { this.speechRecognition.stop(); } catch (error) {
                setVoiceState(`NO SE PUDO PAUSAR STT: ${error.name}: ${error.message}`, "error");
            }
        };

        if (btnPtt) {
            // Toque alterna grabacion continua; salir del boton no interrumpe el dictado.
            btnPtt.addEventListener("click", (event) => {
                if (this.isRecording || this.recognitionStarting) stopRecording(event);
                else startRecording(event);
            });

            const controls = document.createElement("div");
            controls.className = "voice-stt-controls";
            controls.style.cssText = "display:flex; gap:8px; margin-top:8px;";
            const pauseButton = document.createElement("button");
            pauseButton.type = "button";
            pauseButton.className = "eva-btn-action";
            pauseButton.textContent = "PAUSAR";
            pauseButton.addEventListener("click", stopRecording);
            const resumeButton = document.createElement("button");
            resumeButton.type = "button";
            resumeButton.className = "eva-btn-action";
            resumeButton.textContent = "REANUDAR";
            resumeButton.addEventListener("click", startRecording);
            controls.append(pauseButton, resumeButton);
            btnPtt.insertAdjacentElement("afterend", controls);
        }
    }

    /**
     * Androgynous Accelerated TTS Voice Synthesis (Web Speech API + Backend Fallback)
     */
    speakMagi(text) {
        if (!text) return;

        // Una sola ruta de audio: navegador si existe, backend solo como fallback.
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
            return;
        }

        // Servidor Backend Core 1 (aplay / espeak-ng) cuando Chromium no sintetiza.
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

        this.shouldRestartRecognition = false;
        if (this.speechRecognition && (this.isRecording || this.recognitionStarting)) {
            try { this.speechRecognition.stop(); } catch (error) { console.warn("STT stop before dispatch:", error); }
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

            let data;
            try {
                data = await res.json();
            } catch (error) {
                throw new Error(`HTTP ${res.status}: respuesta JSON invalida`);
            }
            const evidence = [];
            if (data.stdout) evidence.push(`[STDOUT]\n${data.stdout}`);
            if (data.stderr) evidence.push(`[STDERR]\n${data.stderr}`);
            if (data.error) evidence.push(`[ERROR]\n${data.error}`);
            if (!evidence.length && data.output) evidence.push(data.output);
            const outputText = evidence.join("\n\n") || `HTTP ${res.status}: respuesta sin evidencia`;

            if (!res.ok || data.success !== true) {
                const failure = `EJECUCION FALLIDA // HTTP ${res.status} // RC ${data.returncode ?? "NO DISPONIBLE"}${data.timed_out ? " // TIMEOUT" : ""}\n${outputText}`;
                if (consoleVoice) consoleVoice.innerText = msgHeader + "\n[-] " + failure;
                if (consoleText) consoleText.innerText = msgHeader + "\n[-] " + failure;
                if (stateVoice) { stateVoice.className = "exec-state-idle"; stateVoice.innerText = "FAILED"; }
                if (stateText) { stateText.className = "exec-state-idle"; stateText.innerText = "FAILED"; }
                this.finishMagiDebate(failure, false, data.summary || outputText);
                return;
            }

            if (consoleVoice) consoleVoice.innerText = msgHeader + "\n[✓] RESPONSE RECEIVED:\n" + outputText;
            if (consoleText) consoleText.innerText = msgHeader + "\n[✓] RESPONSE RECEIVED:\n" + outputText;

            if (stateVoice) { stateVoice.className = "exec-state-done"; stateVoice.innerText = "CONSENSUS REACHED"; }
            if (stateText) { stateText.className = "exec-state-done"; stateText.innerText = "CONSENSUS REACHED"; }

            // Concluir Debate MAGI
            this.finishMagiDebate(outputText, true, data.summary || outputText);

        } catch (e) {
            const errMsg = "Error de enlace con el agente AntiGravity: " + e.message;
            if (consoleVoice) consoleVoice.innerText += "\n[-] " + errMsg;
            if (consoleText) consoleText.innerText += "\n[-] " + errMsg;

            if (stateVoice) { stateVoice.className = "exec-state-idle"; stateVoice.innerText = "FAILED"; }
            if (stateText) { stateText.className = "exec-state-idle"; stateText.innerText = "FAILED"; }

            this.finishMagiDebate(errMsg, false, errMsg);
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
    finishMagiDebate(resultText, isSuccess, ttsSummary = "") {
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
            titleEl.innerText = isSuccess ? "EJECUCION COMPLETADA" : "EJECUCION FALLIDA";
            titleEl.style.color = isSuccess ? "var(--magi-green)" : "var(--magi-red)";
        }
        if (verdictEl) {
            verdictEl.innerText = isSuccess ? "ANTIGRAVITY DEVOLVIO EXITO VERIFICABLE" : resultText.slice(0, 240);
        }

        // Pods reflejan finalizacion; un fallo nunca se presenta como consenso verde.
        ["pod-balthasar", "pod-casper", "pod-melchior"].forEach(id => {
            const podEl = document.getElementById(id);
            if (podEl) {
                podEl.classList.remove("debating");
                if (isSuccess) podEl.classList.add("consensus");
            }
        });

        const bMelchior = document.getElementById("pod-status-melchior");
        const bBalthasar = document.getElementById("pod-status-balthasar");
        const bCasper = document.getElementById("pod-status-casper");

        if (bMelchior) bMelchior.innerText = isSuccess ? "COMPLETED" : "FAILED";
        if (bBalthasar) bBalthasar.innerText = isSuccess ? "COMPLETED" : "FAILED";
        if (bCasper) bCasper.innerText = isSuccess ? "VERIFIED" : "NOT VERIFIED";

        // La locucion usa exclusivamente el resumen natural retornado por el backend.
        if (ttsSummary) this.speakMagi(ttsSummary);

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
