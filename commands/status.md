---
description: "Muestra el estado de la sesión activa de Alfred Dev"
---

# Estado de la sesión

Lee el fichero `.claude/alfred-dev-state.json`. Si no existe, informa de que no hay sesión activa.

Si existe, presenta:
- Comando activo y descripción
- Fase actual y número de fase
- Fases completadas con timestamps y artefactos generados
- Gates pendientes o fallidas
- Dependencias nuevas añadidas
- Hallazgos de seguridad
- Notas acumuladas

Presenta la información de forma legible con tablas y formato claro.
