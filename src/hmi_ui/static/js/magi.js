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
        this.sttPauseTimer = null;
        this.sttPauseMs = Math.min(1200, Math.max(900, Number(window.MAGI_STT_PAUSE_MS) || 1000));
        this.interimTranscript = "";
        this.transcriptArea = null;
        this.recognitionStopReason = null;
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
    cancelSttPauseTimer() {
        if (this.sttPauseTimer !== null) {
            clearTimeout(this.sttPauseTimer);
            this.sttPauseTimer = null;
        }
    }

    renderSttTranscript() {
        if (this.transcriptArea) {
            this.transcriptArea.value = `${this.finalTranscript} ${this.interimTranscript}`.trim();
        }
    }

    scheduleSttPausePunctuation() {
        this.cancelSttPauseTimer();
        this.sttPauseTimer = setTimeout(() => {
            this.sttPauseTimer = null;
            const trimmed = this.finalTranscript.trimEnd();
            if (trimmed && !/[.?!,]$/.test(trimmed)) this.finalTranscript = `${trimmed},`;
            this.renderSttTranscript();
        }, this.sttPauseMs);
    }

    setupPushToTalk() {
        const btnPtt = document.getElementById("btn-push-to-talk");
        const voiceDot = document.getElementById("voice-indicator");
        const statusText = document.getElementById("voice-status-text");
        const transcriptArea = document.getElementById("voice-transcript-output");
        this.transcriptArea = transcriptArea;
        if (transcriptArea?.value?.trim()) this.finalTranscript = transcriptArea.value.trim();

        const setVoiceState = (message, state = "ready") => {
            if (statusText) {
                statusText.innerText = message;
                statusText.setAttribute("role", "status");
                statusText.setAttribute("aria-live", "polite");
                statusText.setAttribute("data-stt-state", state);
            }
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
                if (error?.name === "NotFoundError") {
                    // A Pi without an ALSA capture device must remain usable by text.
                    setVoiceState("MICRÓFONO NO DETECTADO - MODO TEXTO ACTIVO", "error");
                    return false;
                }
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
                let receivedFinal = false;
                this.cancelSttPauseTimer();

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        const fragment = event.results[i][0].transcript.trim();
                        if (fragment) {
                            this.finalTranscript = `${this.finalTranscript} ${fragment}`.trim();
                            receivedFinal = true;
                        }
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }
                this.interimTranscript = interimTranscript.trim();
                this.renderSttTranscript();
                if (receivedFinal) this.scheduleSttPausePunctuation();
            };

            this.speechRecognition.onerror = (event) => {
                console.warn("STT Error:", event.error);
                this.cancelSttPauseTimer();
                this.recognitionStarting = false;
                this.shouldRestartRecognition = false;
                this.isRecording = false;
                this.recognitionStopReason = "error";
                if (event.error === "not-allowed" || event.error === "audio-capture") {
                    setVoiceState("MICRÓFONO NO DETECTADO - MODO TEXTO ACTIVO", "error");
                    return;
                }
                setVoiceState(`ERROR EN STT: ${event.error.toUpperCase()}${event.message ? `: ${event.message}` : ""}`, "error");
            };
            this.speechRecognition.onstart = () => {
                this.recognitionStarting = false;
                this.isRecording = true;
                this.recognitionStopReason = null;
                setVoiceState("GRABACION CONTINUA ACTIVA // PAUSE PARA DETENER", "recording");
            };
            this.speechRecognition.onend = () => {
                this.recognitionStarting = false;
                this.isRecording = false;
                const unexpectedEnd = this.shouldRestartRecognition && this.recognitionStopReason === null;
                if (unexpectedEnd) {
                    setVoiceState("STT INTERRUMPIDO // REINICIANDO CAPTURA", "restarting");
                    window.setTimeout(() => startRecording(), 250);
                } else {
                    const message = this.recognitionStopReason === "execute"
                        ? "STT DETENIDO PARA EJECUTAR"
                        : (this.recognitionStopReason === "error" ? "STT DETENIDO POR ERROR" : "STT PAUSADO // LISTO PARA REANUDAR O EJECUTAR");
                    setVoiceState(message, this.recognitionStopReason === "error" ? "error" : "ready");
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
            this.recognitionStopReason = null;
            this.recognitionStarting = true;
            setVoiceState("INICIANDO MICROFONO...", "recording");
            try {
                this.speechRecognition.start();
            } catch (error) {
                this.recognitionStarting = false;
                this.shouldRestartRecognition = false;
                this.recognitionStopReason = "error";
                setVoiceState(`NO SE PUDO INICIAR STT: ${error.name}: ${error.message}`, "error");
            }
        };

        const stopRecording = (e) => {
            if (e) e.preventDefault();
            this.cancelSttPauseTimer();
            this.shouldRestartRecognition = false;
            this.recognitionStopReason = "user";
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

        // Force synthesis on the Pi so MAGI uses its physical HDMI/jack route.
        try {
            fetch("/api/audio/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, rate: 1.6, pitch: 1.25 })
            }).then(response => {
                if (!response.ok) console.warn("MAGI backend TTS failed", response.status);
            }).catch(error => console.warn("MAGI backend TTS unavailable", error));
        } catch (e) {
            console.warn("MAGI backend TTS unavailable", e);
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

        this.cancelSttPauseTimer();
        this.shouldRestartRecognition = false;
        this.recognitionStopReason = "execute";
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
            const sections = [];
            const pods = Array.isArray(data.pods) ? data.pods : (data.deliberation?.pods || []);
            pods.forEach(pod => sections.push(this.formatMagiResult(
                `${pod.name || pod.id || "POD"} // ${pod.position || "POSICION NO DECLARADA"}`,
                pod.result || {}, pod.success
            )));
            sections.push(this.formatMagiResult("GOLDEN PATH", data.golden_path || {}, data.golden_path_validation?.valid === true));
            if (data.execution_result) {
                sections.push(this.formatMagiResult("BALTHASAR-EXECUTOR", data.execution_result, data.execution_success));
            } else {
                sections.push(`=== BALTHASAR-EXECUTOR ===\nEJECUCION OMITIDA: ${data.execution_skipped_reason || "RAZON NO INFORMADA"}`);
            }
            if (data.summary_degraded) sections.push(`[RESUMEN ORAL DEGRADADO]\n${data.summary_error || "Motivo no informado"}`);
            if (data.error) sections.push(`[ERROR]\n${data.error}`);
            const outputText = sections.join("\n\n") || `HTTP ${res.status}: respuesta sin dictamenes`;
            const pipelineSucceeded = res.ok && data.request_processed === true && data.pipeline_success === true;
            const finalState = this.deriveMagiState(data, res.ok);

            if (consoleVoice) consoleVoice.innerText = msgHeader + `\n[${pipelineSucceeded ? "+" : "-"}] HTTP ${res.status}\n` + outputText;
            if (consoleText) consoleText.innerText = msgHeader + `\n[${pipelineSucceeded ? "+" : "-"}] HTTP ${res.status}\n` + outputText;
            if (stateVoice) { stateVoice.className = pipelineSucceeded ? "exec-state-done" : "exec-state-idle"; stateVoice.innerText = finalState; }
            if (stateText) { stateText.className = pipelineSucceeded ? "exec-state-done" : "exec-state-idle"; stateText.innerText = finalState; }
            this.finishMagiDebate(data, res.ok);

        } catch (e) {
            const errMsg = "Error de enlace con el agente AntiGravity: " + e.message;
            if (consoleVoice) consoleVoice.innerText += "\n[-] " + errMsg;
            if (consoleText) consoleText.innerText += "\n[-] " + errMsg;

            if (stateVoice) { stateVoice.className = "exec-state-idle"; stateVoice.innerText = "FAILED"; }
            if (stateText) { stateText.className = "exec-state-idle"; stateText.innerText = "FAILED"; }

            this.finishMagiDebate(null, false, errMsg);
        }
    }

    formatMagiResult(label, result, success) {
        const lines = [`=== ${label} ===`, `SUCCESS: ${success === true}`, `RC: ${result.returncode ?? "NO DISPONIBLE"}`, `TIMEOUT: ${result.timed_out === true}`, `DURACION_MS: ${result.duration_ms ?? "NO DISPONIBLE"}`];
        if (result.stdout) lines.push(`[STDOUT]\n${result.stdout}`);
        if (result.stderr) lines.push(`[STDERR]\n${result.stderr}`);
        if (!result.stdout && !result.stderr) lines.push("[SIN SALIDA]");
        return lines.join("\n");
    }

    deriveMagiState(data, httpOk) {
        if (!httpOk || data?.request_processed !== true || data?.pipeline_success !== true) return "FALLO DE PIPELINE";
        if (data.consensus?.reached === true && data.execution_success === true) return "CONSENSO // EJECUCION COMPLETA";
        if (data.execution_result == null && data.execution_skipped_reason) {
            return `${data.consensus?.status || "DISENSO"} // EJECUCION OMITIDA`;
        }
        if (data.execution_success === true) return `${data.consensus?.status || "DISENSO"} // EJECUCION COMPLETA`;
        return "FALLO DE PIPELINE";
    }

    /**
     * MAGI Tripartite Deliberation / Consensus Visualizer Routine
     */
    startMagiDebate(promptText) {
        if (this.debateInterval) clearInterval(this.debateInterval);
        this.debateInterval = null;
        this.debateStartTime = Date.now();

        // 2. Banner central de debate
        const banner = document.getElementById("magi-debate-banner");
        const titleEl = document.getElementById("debate-title-text");
        const verdictEl = document.getElementById("debate-verdict-text");
        const queryFooter = document.getElementById("footer-status-query");

        if (banner) banner.style.display = "block";
        if (titleEl) titleEl.innerText = "ESPERANDO DICTAMEN";
        if (verdictEl) verdictEl.innerText = "MELCHIOR // BALTHASAR // CASPER";
        if (queryFooter) queryFooter.innerText = "QUERY: " + promptText.toUpperCase();

        // 3. Estado neutral hasta recibir evidencia del backend.
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
            const badge = document.getElementById(p.badge);
            const fill = document.getElementById(p.fill);
            if (badge) badge.innerText = "ESPERANDO DICTAMEN";
            if (fill) fill.style.width = "0%";
        });
        const bar = document.getElementById("debate-sync-progress");
        if (bar) bar.style.width = "0%";
    }

    /**
     * Finish MAGI Debate & Announce Tripartite Consensus
     */
    finishMagiDebate(data, httpOk, transportError = "") {
        if (this.debateInterval) {
            clearInterval(this.debateInterval);
            this.debateInterval = null;
        }

        const banner = document.getElementById("magi-debate-banner");
        const titleEl = document.getElementById("debate-title-text");
        const verdictEl = document.getElementById("debate-verdict-text");
        const bar = document.getElementById("debate-sync-progress");

        if (bar) bar.style.width = "0%";
        const consensusReached = data?.consensus?.reached === true;
        const consensusStatus = transportError ? "FALLO DE PIPELINE" : this.deriveMagiState(data, httpOk);
        if (titleEl) {
            titleEl.innerText = consensusStatus;
            titleEl.style.color = consensusReached ? "var(--magi-green)"
                : (consensusStatus === "FALLO DE PIPELINE" ? "var(--magi-red)" : "var(--magi-orange)");
        }
        if (verdictEl) {
            verdictEl.innerText = transportError || (data?.execution_skipped_reason
                ? `EJECUCION OMITIDA: ${data.execution_skipped_reason}`
                : (data?.consensus?.vetoes?.length ? `VETOS: ${data.consensus.vetoes.join(", ")}`
                    : `PIPELINE: ${data?.pipeline_success === true ? "COMPLETO" : "FALLIDO"}`));
        }

        // Pods reflejan finalizacion; un fallo nunca se presenta como consenso verde.
        ["pod-balthasar", "pod-casper", "pod-melchior"].forEach(id => {
            const podEl = document.getElementById(id);
            if (podEl) {
                podEl.classList.remove("debating");
                if (consensusReached) podEl.classList.add("consensus");
            }
        });

        const bMelchior = document.getElementById("pod-status-melchior");
        const bBalthasar = document.getElementById("pod-status-balthasar");
        const bCasper = document.getElementById("pod-status-casper");

        const pods = Array.isArray(data?.pods) ? data.pods : (data?.deliberation?.pods || []);
        const badges = { "MELCHIOR-1": bMelchior, "BALTHASAR-2": bBalthasar, "CASPER-3": bCasper };
        pods.forEach(pod => {
            const badge = badges[pod.name];
            if (badge) badge.innerText = pod.success === true ? (pod.position || "POSICION NO DECLARADA") : `FALLO${pod.result?.timed_out ? " // TIMEOUT" : ""}`;
        });
        Object.values(badges).forEach(badge => {
            if (badge && !pods.some(pod => badges[pod.name] === badge)) badge.innerText = "SIN EVIDENCIA";
        });

        // La locucion usa exclusivamente el resumen natural retornado por el backend.
        if (typeof data?.summary === "string" && data.summary.trim()) this.speakMagi(data.summary.trim());

        // El resultado permanece visible hasta la siguiente deliberacion.
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
            const powerEl = document.getElementById("status-power");
            const rtEl = document.getElementById("status-rt-core");

            if (tempEl) tempEl.innerText = `${data.cpu_temp} °C`;
            if (wifiEl) wifiEl.innerText = data.wifi_connected ? data.wifi_ssid : "ETH0 DIRECT LINK";
            if (ipEl) ipEl.innerText = data.ip_address;
            if (powerEl) {
                const power = data.power || {};
                const voltage = Number.isFinite(power.core_voltage_v) ? `${power.core_voltage_v.toFixed(3)} V` : "N/D";
                const current = Number.isFinite(power.current_a) ? `${power.current_a.toFixed(3)} A` : "N/D";
                const watts = Number.isFinite(power.power_w) ? `${power.power_w.toFixed(3)} W` : "N/D";
                powerEl.innerText = `VCORE: ${voltage} // I: ${current} // P: ${watts}`;
            }
            if (rtEl) {
                rtEl.innerText = data.rt_alive ? "CORE 3 RT ALIVE" : "ACTIVE / CORE 3";
                rtEl.style.color = data.rt_alive ? "var(--magi-green)" : "var(--magi-orange)";
            }

            // Melchior Telemetry Cards: no sintetizar mediciones ausentes.
            const telemSpeed = document.getElementById("telem-speed");
            if (telemSpeed && data.speed_rad_s != null) telemSpeed.innerText = `${data.speed_rad_s} rad/s`;
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
