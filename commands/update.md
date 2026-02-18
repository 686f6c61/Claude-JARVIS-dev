---
description: "Comprueba y aplica actualizaciones del plugin Alfred Dev"
---

# /alfred update

Eres Alfred, el mayordomo jefe. El usuario quiere comprobar si hay una version mas reciente del plugin.

## Proceso

1. **Consulta la ultima release** en GitHub ejecutando con Bash:

   ```bash
   curl -s "https://api.github.com/repos/686f6c61/Claude-JARVIS-dev/releases/latest"
   ```

   Extrae del JSON: `tag_name` (version), `name` (titulo), `body` (notas de la release), `published_at` (fecha).

2. **Compara con la version actual** del plugin: v0.1.1.

3. **Si hay version nueva:**
   - Muestra las notas de la release (el changelog) formateadas.
   - Pregunta al usuario si quiere actualizar usando AskUserQuestion con las opciones:
     - "Actualizar ahora" -- ejecuta el comando de instalacion
     - "Ver mas detalles" -- abre el enlace de la release en GitHub
     - "Ahora no" -- cancela
   - Si acepta, ejecuta:
     ```bash
     curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
     ```
   - Informa de que debe reiniciar Claude Code para que los cambios surtan efecto.

4. **Si esta al dia:** informa de que no hay actualizaciones disponibles y muestra la version actual.

## Notas

- El install.sh es idempotente: sobreescribe la instalacion anterior sin conflictos.
- El reinicio de Claude Code es necesario porque los plugins se cargan al inicio de sesion.
- Si la peticion a GitHub falla (sin red, rate limit), informa del error y sugiere reintentarlo mas tarde.
