---
description: "Protocolo de respuesta ante incidentes: triaje, mitigacion, RCA y postmortem"
---

# Respuesta ante incidentes

El usuario ha reportado o detectado un incidente en produccion. Sigue este protocolo paso a paso para gestionar la respuesta de forma estructurada, desde el triaje inicial hasta el postmortem final.

## Contexto

Los incidentes en produccion requieren una respuesta rapida pero ordenada. La tentacion es saltar directamente al codigo, pero sin un triaje previo se pierde tiempo en diagnosticos erroneos. Este protocolo garantiza que cada paso se documenta y que las lecciones aprendidas quedan registradas para evitar recurrencias.

## Protocolo

### Fase 1: Triaje (qa-engineer)

Usa la herramienta Task para lanzar al agente `qa-engineer` con la siguiente mision:

1. Clasificar la severidad del incidente (P0 critico, P1 alto, P2 medio, P3 bajo).
2. Identificar el impacto: usuarios afectados, funcionalidad comprometida, datos en riesgo.
3. Recopilar evidencia: logs, trazas, capturas, mensajes de error.
4. Definir si hay workaround inmediato.

**Artefacto:** informe de triaje con severidad, impacto y evidencia.

### Fase 2: Mitigacion (senior-dev)

Si el triaje indica P0 o P1, ejecutar mitigacion inmediata:

1. Aplicar workaround si existe (rollback, feature flag, redirect de trafico).
2. Si no hay workaround, desarrollar hotfix minimo con test de regresion.
3. Desplegar la mitigacion y verificar que el impacto se reduce.

**Artefacto:** commit de mitigacion con test de regresion.

### Fase 3: Analisis de causa raiz (senior-dev + security-officer)

Una vez mitigado el impacto, investigar la causa raiz:

1. Trazar la cadena de eventos desde el trigger hasta el fallo.
2. Identificar la causa raiz (no el sintoma).
3. Si el incidente tiene componente de seguridad, el security-officer audita la cadena.
4. Registrar la causa raiz como decision en la memoria del proyecto.

**Artefacto:** documento de RCA (Root Cause Analysis).

### Fase 4: Postmortem

Generar un informe postmortem completo:

1. Cronologia del incidente (cuando se detecto, cuando se mitigo, cuando se resolvio).
2. Causa raiz confirmada.
3. Acciones correctivas con responsable y fecha limite.
4. Acciones preventivas para evitar recurrencia.
5. Lecciones aprendidas.

**Artefacto:** documento postmortem en formato Markdown.

## Formato del postmortem

```markdown
# Postmortem: [titulo del incidente]

**Fecha:** YYYY-MM-DD
**Severidad:** P0/P1/P2/P3
**Duracion:** X horas/minutos
**Impacto:** [descripcion del impacto]

## Cronologia
- HH:MM - [evento]
- HH:MM - [evento]

## Causa raiz
[Explicacion detallada]

## Acciones correctivas
- [ ] [accion] - Responsable: [nombre] - Fecha: YYYY-MM-DD

## Acciones preventivas
- [ ] [accion] - Responsable: [nombre] - Fecha: YYYY-MM-DD

## Lecciones aprendidas
1. [leccion]
```
