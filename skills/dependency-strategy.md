---
description: "Estrategia de dependencias: evaluacion, licencias, vulnerabilidades y actualizaciones"
---

# Estrategia de dependencias

El usuario quiere evaluar, auditar o planificar la gestion de dependencias del proyecto. Este skill proporciona un marco estructurado para tomar decisiones informadas sobre que dependencias incorporar, cuales actualizar y cuales retirar.

## Contexto

Las dependencias son una de las mayores fuentes de riesgo en un proyecto de software: vulnerabilidades de seguridad, licencias incompatibles, abandonware y bloat innecesario. En entornos corporativos, cada dependencia es un contrato implicito de mantenimiento. Este skill ayuda a gestionar ese riesgo de forma sistematica.

## Protocolo

### Fase 1: Inventario (security-officer)

1. Listar todas las dependencias directas y transitivas del proyecto.
2. Para cada dependencia, recopilar:
   - Version actual vs ultima version disponible.
   - Licencia (MIT, Apache-2.0, GPL, etc.).
   - Ultimo commit/release (actividad del mantenedor).
   - Vulnerabilidades conocidas (CVEs abiertos).
   - Tamano del paquete (impacto en bundle/build).

**Herramientas:** `npm audit`, `pip audit`, `cargo audit`, `gh api advisories` segun el ecosistema.

**Artefacto:** tabla de inventario de dependencias.

### Fase 2: Evaluacion de riesgo

Clasificar cada dependencia en una matriz de riesgo:

| Criterio | Bajo | Medio | Alto |
|----------|------|-------|------|
| CVEs abiertos | 0 | 1-2 (no criticos) | Cualquier critico |
| Licencia | MIT, Apache-2.0, ISC | BSD, MPL | GPL, AGPL, sin licencia |
| Actividad | Release en ultimos 6 meses | Release en ultimo ano | Sin releases en >1 ano |
| Alternativas | Sin alternativa viable | Alternativas parciales | Multiples alternativas mejores |

### Fase 3: Plan de accion

Para cada dependencia de riesgo medio o alto, definir una accion:

| Accion | Cuando aplicar |
|--------|----------------|
| **Actualizar** | Version desactualizada con parches disponibles |
| **Reemplazar** | Dependencia abandonada con alternativas mejores |
| **Eliminar** | Dependencia innecesaria (funcionalidad duplicada o infrautilizada) |
| **Aceptar riesgo** | Sin alternativa, impacto controlado, mitigacion aplicada |
| **Fijar version** | Dependencia estable que no conviene actualizar automaticamente |

### Fase 4: Politica de actualizaciones

Establecer una politica de actualizaciones para el proyecto:

1. **Patch versions:** actualizar automaticamente (Dependabot, Renovate).
2. **Minor versions:** revisar changelog, actualizar en sprint de mantenimiento.
3. **Major versions:** evaluar breaking changes, planificar migracion.
4. **Dependencias de seguridad:** actualizar inmediatamente, sin esperar a sprint.

### Fase 5: Documentacion

Registrar las decisiones de dependencias en la memoria del proyecto usando `memory_log_decision`:

- Dependencias rechazadas y motivo.
- Dependencias aceptadas con riesgo y mitigacion.
- Politica de actualizaciones acordada.

**Artefacto:** documento de estrategia de dependencias + decisiones registradas en memoria.
