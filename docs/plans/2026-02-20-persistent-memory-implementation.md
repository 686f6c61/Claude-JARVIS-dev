# Memoria persistente -- plan de implementacion

> **Para Claude:** SKILL OBLIGATORIO: usar superpowers:executing-plans para implementar este plan tarea a tarea.

**Objetivo:** implementar la capa de memoria persistente por proyecto para Alfred Dev v0.2.0, con agente Bibliotecario, MCP server local y captura automatica de eventos.

**Arquitectura:** API Python pura en `core/memory.py` (sqlite3 stdlib) + MCP server stdio persistente (`mcp/memory_server.py`) + hook de captura automatica (`hooks/memory-capture.py`) + agente opcional Bibliotecario (`agents/optional/librarian.md`). Cero cambios en `orchestrator.py`.

**Stack:** Python 3.10+, sqlite3 (stdlib), protocolo MCP stdio, YAML frontmatter para agente.

**Diseno de referencia:** `docs/plans/2026-02-20-persistent-memory-design.md`

---

## Tarea 1: core/memory.py -- clase MemoryDB y esquema

El modulo fundacional. Todo lo demas depende de el.

**Ficheros:**
- Crear: `core/memory.py`
- Test: `tests/test_memory.py`

**Paso 1: escribir los tests que fallan**

Crear `tests/test_memory.py` con las clases de test basicas: `TestMemoryDBCreation` (verifica tablas, schema_version, WAL, foreign keys, deteccion FTS5, permisos 0600). Usar `tempfile.NamedTemporaryFile` para la DB y limpiar en `tearDown`.

Importar:
```python
from core.memory import MemoryDB
```

**Paso 2: ejecutar tests para verificar que fallan**

Ejecutar: `python3 -m pytest tests/test_memory.py -v`
Esperado: FAIL con `ModuleNotFoundError: No module named 'core.memory'`

**Paso 3: implementar core/memory.py**

Crear el modulo con:

1. **Constantes de sanitizacion**: compilar los mismos patrones regex de `secret-guard.sh` (ver lineas 89-96 del fichero actual). Cada patron se compila con `re.compile` y se asocia a una etiqueta. IMPORTANTE: en los tests, usar patrones que parezcan secretos pero que sean claramente ficticios (prefijo correcto + caracteres aleatorios). No copiar claves de ejemplo de documentacion oficial.

2. **Funcion `sanitize_content(text)`**: aplica los patrones y reemplaza por `[REDACTED:<etiqueta>]`.

3. **Clase `MemoryDB`**:
   - Constructor: recibe `db_path`, crea directorios, abre conexion, activa WAL y FK, llama a `_ensure_schema()` y `_detect_fts5()`, aplica permisos 0600.
   - `_ensure_schema()`: ejecuta el SQL de creacion (6 tablas + 5 indices), registra `schema_version=1` en meta si es primera vez.
   - `_detect_fts5()`: intenta crear tabla virtual FTS5 temporal. Si funciona, crea `memory_fts`. Registra resultado en meta.
   - **Escritura**: `start_iteration()`, `complete_iteration()`, `log_decision()`, `log_commit()`, `link_commit_decision()`, `log_event()`. Todas sanitizan texto antes de persistir.
   - **Lectura**: `get_iteration()`, `get_active_iteration()`, `get_decisions()`, `search()`, `get_timeline()`, `get_stats()`.
   - `search()`: usa FTS5 MATCH si disponible, LIKE fallback si no. Enriquece resultados con datos completos.
   - `purge_old_events(retention_days)`: borra eventos antiguos. Solo eventos, no decisiones.
   - `close()`: cierra la conexion.

El esquema SQL completo esta en el documento de diseno (seccion 4).

**Paso 4: ejecutar tests**

Ejecutar: `python3 -m pytest tests/test_memory.py -v`
Esperado: todos PASS

**Paso 5: commit**

```bash
git add core/memory.py tests/test_memory.py
git commit -m "feat: modulo core/memory.py con MemoryDB, esquema y tests"
```

---

## Tarea 2: tests completos de operaciones CRUD y busqueda

Ampliar la cobertura de tests.

**Ficheros:**
- Modificar: `tests/test_memory.py`

**Paso 1: anadir tests de CRUD**

Anadir clases:
- `TestIterations`: start/get/complete/active/latest
- `TestDecisions`: log/get/auto-link a iteracion activa
- `TestCommits`: log/duplicado ignorado/vinculacion con decisiones
- `TestSanitization`: patron AWS redactado, JWT redactado, None devuelve None, texto limpio sin cambios. NOTA: generar strings que coincidan con los patrones regex pero que sean claramente ficticios (no copiar claves de documentacion).
- `TestSearch`: busqueda por decision, por commit, termino sin resultados
- `TestEvents`: log/timeline/purge
- `TestStats`: contadores y metadata

Importar tambien `sanitize_content` desde `core.memory`.

**Paso 2: ejecutar tests**

Ejecutar: `python3 -m pytest tests/test_memory.py -v`
Esperado: todos PASS

**Paso 3: commit**

```bash
git add tests/test_memory.py
git commit -m "test: cobertura completa de CRUD, busqueda y sanitizacion en memory"
```

---

## Tarea 3: MCP server (mcp/memory_server.py)

Servidor MCP stdio que expone las 6 herramientas del Bibliotecario.

**Ficheros:**
- Crear: `mcp/memory_server.py`
- Crear: `mcp/__init__.py` (vacio)
- Crear: `.claude-plugin/mcp.json`

**Paso 1: investigar el protocolo MCP stdio**

Antes de implementar, consultar la documentacion de MCP para Python. Buscar como otros plugins del ecosistema implementan sus servers MCP. Revisar si el paquete `mcp` esta disponible en el entorno o si hay que implementar el protocolo JSON-RPC sobre stdin/stdout a mano.

Dado que el plugin no puede depender de paquetes externos, la implementacion debe funcionar solo con stdlib. El formato del protocolo MCP stdio es:
- Lectura: `Content-Length: N\r\n\r\n{JSON-RPC}`
- Escritura: `Content-Length: N\r\n\r\n{JSON-RPC}`

**Paso 2: implementar el server**

Crear `mcp/memory_server.py` con:

1. Clase `MemoryMCPServer` que encapsula el loop de lectura/escritura JSON-RPC
2. Handler `initialize` que devuelve capacidades y metadata del server
3. Handler `tools/list` que devuelve las 6 herramientas con sus JSON Schemas:
   - `memory_search`: params `query` (str, required), `limit` (int, optional), `iteration_id` (int, optional)
   - `memory_log_decision`: params `title` (str, required), `chosen` (str, required), `context` (str, optional), `alternatives` (array, optional), `rationale` (str, optional), `impact` (str, optional), `phase` (str, optional)
   - `memory_log_commit`: params `sha` (str, required), `message` (str, optional), `decision_ids` (array, optional), `iteration_id` (int, optional)
   - `memory_get_iteration`: params `id` (int, optional)
   - `memory_get_timeline`: params `iteration_id` (int, required)
   - `memory_stats`: sin params
4. Handler `tools/call` que despacha al metodo correspondiente de `MemoryDB`
5. Resolucion de ruta: `os.path.join(os.getcwd(), ".claude", "alfred-memory.db")`
6. Al arrancar: abrir DB, ensure_schema, detect_fts5, purge si retention_days configurado

**Paso 3: crear mcp.json**

Crear `.claude-plugin/mcp.json`:

```json
{
  "mcpServers": {
    "alfred-memory": {
      "type": "stdio",
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/memory_server.py"]
    }
  }
}
```

**Paso 4: test manual**

Ejecutar el server y enviar un mensaje `initialize` por stdin para verificar que responde correctamente.

**Paso 5: commit**

```bash
git add mcp/ .claude-plugin/mcp.json
git commit -m "feat: MCP server stdio para memoria persistente"
```

---

## Tarea 4: hook de captura automatica (hooks/memory-capture.py)

Hook PostToolUse/Write que detecta escrituras en `alfred-dev-state.json` y registra eventos.

**Ficheros:**
- Crear: `hooks/memory-capture.py`
- Modificar: `hooks/hooks.json`

**Paso 1: implementar el hook**

Crear `hooks/memory-capture.py`:

1. Leer JSON de stdin (entrada del hook PostToolUse)
2. Extraer `file_path` de `tool_input`
3. Si no termina en `alfred-dev-state.json`, exit 0
4. Comprobar si memoria esta habilitada (buscar `memoria:` + `enabled: true` en `alfred-dev.local.md`)
5. Leer el estado nuevo del fichero
6. Importar `MemoryDB` de `core.memory`
7. Comparar con el estado almacenado en la DB:
   - Si no hay iteracion activa: `start_iteration()` + evento `iteration_started`
   - Si hay mas fases completadas que antes: `log_event("phase_completed")` por cada nueva
   - Si fase_actual es "completado": `complete_iteration()` + evento `iteration_completed`
8. Siempre exit 0 (nunca bloquear)

**Paso 2: registrar en hooks.json**

Anadir al array de `PostToolUse`:

```json
{
    "matcher": "Write|Edit",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/memory-capture.py",
            "timeout": 10
        }
    ]
}
```

**Paso 3: commit**

```bash
git add hooks/memory-capture.py hooks/hooks.json
git commit -m "feat: hook de captura automatica de eventos en memoria"
```

---

## Tarea 5: agente Bibliotecario (agents/optional/librarian.md)

**Ficheros:**
- Crear: `agents/optional/librarian.md`
- Modificar: `.claude-plugin/plugin.json` (registrar agente)
- Modificar: `core/personality.py` (anadir personalidad)
- Modificar: `core/config_loader.py` (anadir a agentes_opcionales)

**Paso 1: crear el agente**

Crear `agents/optional/librarian.md` con frontmatter YAML identico al formato de `copywriter.md`:

```yaml
---
name: librarian
description: |
  Usar para consultar la memoria persistente del proyecto: decisiones, iteraciones,
  commits y cronologia. Se activa cuando el usuario pregunta por historico o cuando
  Alfred necesita contexto de sesiones anteriores.
  [3 examples con commentary siguiendo el patron de copywriter.md]
tools: Read
model: sonnet
color: yellow
---
```

Cuerpo del prompt:
- Identidad: El Bibliotecario, archivista riguroso
- Regla HARD-GATE: siempre citar fuente con ID/fecha/iteracion
- Clasificacion de preguntas (decision, implementacion, cronologia, estadistica)
- Formato de respuesta (resumen + evidencia + contexto)
- Frases tipicas para cada nivel de sarcasmo
- Cadena de integracion (activado por Alfred, reporta a Alfred)

**Paso 2: registrar en plugin.json**

Anadir `"./agents/optional/librarian.md"` al array `agents`.

**Paso 3: anadir personalidad en personality.py**

Anadir entrada `"librarian"` al dict `AGENTS` con: nombre_display, rol, color, modelo, personalidad, frases_habituales, frases_sarcasmo_alto.

**Paso 4: anadir a DEFAULT_CONFIG en config_loader.py**

Anadir `"librarian": False` al dict `agentes_opcionales`.

**Paso 5: commit**

```bash
git add agents/optional/librarian.md .claude-plugin/plugin.json core/personality.py core/config_loader.py
git commit -m "feat: agente El Bibliotecario para consultas de memoria"
```

---

## Tarea 6: modificar session-start.sh para inyectar contexto de memoria

**Ficheros:**
- Modificar: `hooks/session-start.sh`

**Paso 1: anadir seccion de memoria**

Despues del bloque de "Estado de sesion activa" (linea 136) y antes de "Comprobacion de actualizaciones" (linea 138), anadir:

1. Comprobar si `.claude/alfred-memory.db` existe
2. Si existe, ejecutar `python3 -c` que:
   - Importa `core.memory.MemoryDB` (con PYTHONPATH apuntando al plugin)
   - Abre la DB
   - Lee ultimas 5 decisiones (titulo + fecha + comando de iteracion)
   - Formatea bloque de contexto
3. Anadir al CONTEXT si hay datos

El bloque tiene este formato:

```
### Memoria del proyecto

El proyecto tiene memoria persistente activa. Ultimas decisiones:

- [fecha] titulo (iteracion: comando #id)
...

Para consultas historicas detalladas, delega en El Bibliotecario.
```

El script Python dentro del bash debe estar envuelto en try/except para no romper session-start si la DB esta corrupta.

**Paso 2: commit**

```bash
git add hooks/session-start.sh
git commit -m "feat: inyeccion de contexto de memoria en session-start"
```

---

## Tarea 7: modificar el prompt de Alfred para delegar al Bibliotecario

**Ficheros:**
- Modificar: `agents/alfred.md`

**Paso 1: anadir instrucciones de delegacion**

Buscar la seccion de agentes opcionales o cadena de integracion en `agents/alfred.md`. Anadir un bloque (10-15 lineas) que explique:

- Cuando delegar al Bibliotecario: preguntas historicas, inicio de flujos feature/fix
- Como: usar herramienta Task con subagente `librarian`
- Que hacer con la respuesta: incorporar al contexto del flujo actual

**Paso 2: commit**

```bash
git add agents/alfred.md
git commit -m "feat: Alfred delega consultas historicas al Bibliotecario"
```

---

## Tarea 8: configuracion de memoria en /alfred config

**Ficheros:**
- Modificar: `commands/config.md`

**Paso 1: anadir seccion de memoria**

Anadir al comando config la logica para:

1. Mostrar estado de memoria (enabled/disabled, modo FTS, estadisticas si activa)
2. Preguntar si quiere activar/desactivar con AskUserQuestion
3. Si activa: escribir seccion `memoria:` en frontmatter de `alfred-dev.local.md`
4. Opciones configurables: `enabled`, `capture_decisions`, `capture_commits`, `retention_days`

**Paso 2: commit**

```bash
git add commands/config.md
git commit -m "feat: seccion de memoria en /alfred config"
```

---

## Tarea 9: version bump y documentacion

**Ficheros:**
- Modificar: 6 ficheros de version (0.1.5 -> 0.2.0)
- Modificar: `README.md`
- Modificar: `site/index.html`

**Paso 1: bump de version a 0.2.0**

Reemplazar `0.1.5` por `0.2.0` en:
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `package.json`
- `hooks/session-start.sh` (CURRENT_VERSION)
- `install.sh` (VERSION)
- `install.ps1` ($Version)

**Paso 2: actualizar README**

- Anadir seccion "Memoria persistente" despues de "Hooks"
- Actualizar cifras: 7 agentes opcionales, 7 hooks
- Documentar: que es, como activar, que captura, el Bibliotecario

**Paso 3: actualizar landing page**

Actualizar `site/index.html`: version a 0.2.0, seccion de memoria.

**Paso 4: commit**

```bash
git add .
git commit -m "feat: v0.2.0 -- memoria persistente de decisiones"
```

---

## Tarea 10: tests de integracion y release

**Paso 1: ejecutar todos los tests**

Ejecutar: `python3 -m pytest tests/ -v`
Esperado: todos PASS

**Paso 2: verificar integracion**

```bash
python3 -c "import json; json.load(open('hooks/hooks.json'))"
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
python3 -c "import json; json.load(open('.claude-plugin/mcp.json'))"
```

**Paso 3: tag y release**

```bash
git tag v0.2.0
git push origin main --tags
gh release create v0.2.0 --title "v0.2.0 -- Memoria persistente de decisiones" --notes "..."
```

**Paso 4: desplegar landing en gh-pages**

Copiar `site/index.html` a rama `gh-pages` (mismo flujo que v0.1.5).

---

## Orden de dependencias

```
Tarea 1 (core/memory.py)
  |
  v
Tarea 2 (tests CRUD)
  |
  +----------+-----------+
  |          |           |
  v          v           v
Tarea 3    Tarea 4     Tarea 5
(MCP)      (hook)      (agente)
  |          |           |
  +----------+-----------+
  |
  v
Tarea 6 (session-start)
  |
  +----------+
  |          |
  v          v
Tarea 7    Tarea 8
(Alfred)   (config)
  |          |
  +----------+
  |
  v
Tarea 9 (version + docs)
  |
  v
Tarea 10 (validacion + release)
```

Las tareas 3, 4 y 5 pueden ejecutarse en paralelo tras completar 1 y 2.
Las tareas 7 y 8 pueden ejecutarse en paralelo.
