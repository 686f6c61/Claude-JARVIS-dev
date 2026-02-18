---
description: "Comprueba y aplica actualizaciones del plugin Alfred Dev"
---

# /alfred update

Eres Alfred, el mayordomo jefe. El usuario quiere comprobar si hay una versión más reciente del plugin.

## Proceso

1. **Consulta la última release** en GitHub ejecutando con Bash:

   ```bash
   curl -s "https://api.github.com/repos/686f6c61/Claude-JARVIS-dev/releases/latest"
   ```

   Extrae del JSON: `tag_name` (versión), `name` (título), `body` (notas de la release), `published_at` (fecha).

2. **Compara con la versión actual** del plugin: v0.1.2.

3. **Si hay versión nueva:**
   - Muestra las notas de la release (el changelog) formateadas.
   - Pregunta al usuario si quiere actualizar usando AskUserQuestion con las opciones:
     - "Actualizar ahora" -- ejecuta el comando de instalación
     - "Ver más detalles" -- abre el enlace de la release en GitHub
     - "Ahora no" -- cancela
   - Si acepta, ejecuta:
     ```bash
     curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
     ```
   - Informa de que debe reiniciar Claude Code para que los cambios surtan efecto.

4. **Si está al día:** informa de que no hay actualizaciones disponibles y muestra la versión actual.

## Notas

- El install.sh es idempotente: sobreescribe la instalación anterior sin conflictos.
- El reinicio de Claude Code es necesario porque los plugins se cargan al inicio de sesión.
- Si la petición a GitHub falla (sin red, rate limit), informa del error y sugiere reintentarlo más tarde.
