# Directivas de Operación y Gobernanza para Agentes Antigravity

Este archivo establece las reglas operacionales, de verificación y de higiene que **todos los agentes de IA** deben cumplir de manera estricta y sin excepciones al interactuar con el repositorio y la estación de trabajo HIL-RTOS.

---

## 1. Reglas Maestras No Negociables (Non-Negotiable Core Rules)

1. **Evidencia Literal Obligatoria:**
   > *Nunca declares un fix o servicio funcionando sin pegar el output literal y completo del comando que lo demuestra (`systemctl status`, `grep`, `verify-input-stack.sh`, etc.). Queda estrictamente prohibido el uso de lenguaje triunfalista o asunciones de éxito sin pruebas adjuntas.*

2. **Aislamiento Atómico de Variables:**
   > *Nunca reescribas más de un archivo de configuración por intento de fix. Cambia una sola variable, verifica su efecto de forma aislada e incremental, y solo entonces decide el siguiente paso. Prohibido realizar cambios simultáneos en navegador, compositor, gestor de asiento y reglas udev.*

3. **Inmutabilidad y Preservación de Historial:**
   > *Nada se borra directamente si existe cualquier duda sobre su uso. Se crea un tag previo en Git (`pre-cleanup-YYYYMMDD`) y los archivos obsoletos o de diagnóstico se mueven a `_archive/` preservando la jerarquía de directorios.*

---

## 2. Agente de Verificación Post-Deploy (Post-Deployment Verification)

Tras cualquier modificación o despliegue en:
- `config/systemd/magi-kiosk.service` (o `/etc/systemd/system/magi-kiosk.service`)
- `config/labwc/environment` (o `~/.config/labwc/environment`)
- `config/labwc/rc.xml` (o `~/.config/labwc/rc.xml`)

El agente debe ejecutar de forma obligatoria el script de verificación:
```bash
bash scripts/verify-input-stack.sh
```
O el equivalente remoto vía SSH:
```bash
python scripts/automation/deploy_magi_remote.py
```

### Criterio de Aceptación:
El agente **únicamente** puede reportar el servicio como "Operativo" si el comando devuelve:
1. `seatd`, `magi-ui` y `magi-kiosk` en estado `active (running)`.
2. El proceso `labwc` contiene explícitamente `WLR_BACKENDS=drm,libinput` en su entorno (`/proc/$PID/environ`).
3. El log del journal no contiene errores fatales de libinput.
4. Se solicita explícitamente la confirmación táctil o visual al operador si se requiere validación de interfaz física.

---

## 3. Agente de Higiene de Repositorio (Repository Hygiene & Housekeeping)

El agente de mantenimiento periódico (mensual o por Pull Request) debe:
1. Ejecutar el inventario completo de archivos:
   ```bash
   find . -type f -not -path './.git/*' -not -path './_archive/*' | sort
   ```
2. Comparar la lista contra `docs/canonical-state/full-file-inventory.txt` y `docs/cleanup-log.md`.
3. Detectar scripts o archivos temporales (`test_*.py`, `tmp_*`, `.bak`, `.log`) con más de 30 días sin clasificar.
4. **Comportamiento del Agente:** No borrar archivos automáticamente. Generar una propuesta de limpieza señalando los archivos candidatos a ser movidos a `_archive/`.

---

## 4. Estándar de Comunicación y Reportes

- Todos los reportes deben contener bloques de código con los outputs literales de consola.
- Los enlaces a archivos deben usar formato Markdown estándar con rutas relativas o URI (`file:///...`).
- Mantener la integridad de los comentarios y docstrings del código existente.
