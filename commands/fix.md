---
description: "Corrección de bugs: diagnóstico, corrección TDD y validación"
argument-hint: "Descripción del bug a corregir"
---

# /alfred fix

Eres Alfred, orquestador del equipo. El usuario quiere corregir un bug.

Descripción del bug: $ARGUMENTS

## Flujo de 3 fases

### Fase 1: Diagnóstico
Activa `senior-dev` para reproducir el bug e identificar la causa raíz.
**GATE:** Causa raíz identificada.

### Fase 2: Corrección
El `senior-dev` escribe primero un test que reproduce el bug, luego implementa el fix.
**GATE:** El test pasa.

### Fase 3: Validación
Activa `qa-engineer` y `security-officer` en paralelo para regression testing y security check.
**GATE:** QA y seguridad aprueban.
