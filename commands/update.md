---
description: "Comprueba y aplica actualizaciones del plugin Alfred Dev"
---

# Actualizar Alfred Dev

Eres Alfred. El usuario quiere comprobar si hay una version nueva del plugin. Sigue estos pasos al pie de la letra.

## Paso 1: obtener la version instalada

Ejecuta con Bash:

```bash
cat ~/.claude/plugins/cache/alfred-dev/*/.claude-plugin/plugin.json 2>/dev/null | python3 -c "import json,sys; [print(json.load(f).get('version','desconocida')) for f in [sys.stdin]]" 2>/dev/null || echo "desconocida"
```

Si no se puede leer, busca la version en el fichero `plugin.json` mas cercano dentro de `~/.claude/plugins/cache/alfred-dev/`.

## Paso 2: consultar la ultima release en GitHub

Ejecuta con Bash:

```bash
curl -s --max-time 10 "https://api.github.com/repos/686f6c61/Claude-JARVIS-dev/releases/latest"
```

Extrae del JSON: `tag_name` (version), `name` (titulo), `body` (notas de la release), `published_at` (fecha).

Si la peticion falla (sin red, rate limit, timeout), informa del error y sugiere reintentarlo mas tarde. No sigas adelante.

## Paso 3: comparar versiones

Compara `tag_name` (sin la `v` inicial) con la version instalada del paso 1.

### Si hay version nueva

Muestra al usuario:
- La version actual instalada
- La version nueva disponible
- Las notas de la release formateadas en markdown

Pregunta al usuario si quiere actualizar usando AskUserQuestion con las opciones:
- **"Actualizar ahora"** -- ejecuta el comando de instalacion (paso 4)
- **"Ahora no"** -- cancela

### Si esta al dia

Informa de que no hay actualizaciones disponibles y muestra la version actual. Fin.

## Paso 4: ejecutar la actualizacion

Si el usuario acepta, ejecuta con Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/Claude-JARVIS-dev/main/install.sh | bash
```

Despues de que termine, informa al usuario de que **debe reiniciar Claude Code** (cerrar y volver a abrir) para que los cambios surtan efecto. Los plugins se cargan al inicio de sesion.

## Notas

- El `install.sh` es idempotente: sobreescribe la instalacion anterior sin conflictos.
- No hace falta desinstalar primero.
- Si el script de instalacion falla, muestra el error completo al usuario.
