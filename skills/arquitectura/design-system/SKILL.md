---
name: design-system
description: "Usar para diseñar la arquitectura de un sistema con diagramas y contratos"
---

# Diseñar arquitectura del sistema

## Resumen

Este skill produce el diseño arquitectónico de un sistema o módulo, incluyendo diagramas de componentes, contratos entre módulos y decisiones de diseño fundamentales. El resultado es un documento que permite a cualquier desarrollador del equipo entender cómo encajan las piezas antes de escribir código.

La arquitectura no se diseña para impresionar, sino para comunicar. Los diagramas deben ser claros, los contratos precisos y las decisiones justificadas.

## Proceso

1. **Entender los requisitos.** Leer el PRD si existe. Identificar los requisitos funcionales (qué hace el sistema) y los no funcionales (rendimiento, escalabilidad, seguridad, disponibilidad). Los requisitos no funcionales suelen ser los que más condicionan la arquitectura.

2. **Definir los componentes principales.** Identificar los módulos, servicios o capas del sistema. Para cada componente, documentar:

   - Responsabilidad principal (una sola, siguiendo SRP).
   - Inputs que recibe.
   - Outputs que produce.
   - Dependencias externas.

3. **Generar diagrama de componentes con Mermaid:**

   ```mermaid
   graph TD
     A[Cliente] --> B[API Gateway]
     B --> C[Servicio Auth]
     B --> D[Servicio Core]
     D --> E[(Base de datos)]
     D --> F[Cola de mensajes]
   ```

   El diagrama debe mostrar los componentes y sus relaciones, no los detalles internos de cada uno.

4. **Generar diagrama de secuencia para los flujos críticos:**

   ```mermaid
   sequenceDiagram
     participant U as Usuario
     participant A as API
     participant D as DB
     U->>A: POST /recurso
     A->>D: INSERT
     D-->>A: OK
     A-->>U: 201 Created
   ```

   Cubrir al menos el happy path y el principal flujo de error.

5. **Definir contratos entre módulos.** Para cada interfaz entre componentes, especificar:

   - Formato de datos (tipos, esquemas).
   - Protocolo de comunicación (HTTP, gRPC, eventos, etc.).
   - Manejo de errores (códigos, reintentos, fallbacks).
   - Versionado del contrato.

6. **Aplicar principios SOLID.** Verificar que el diseño respeta:

   - **S**ingle Responsibility: cada componente tiene una razón para cambiar.
   - **O**pen/Closed: extensible sin modificar lo existente.
   - **L**iskov Substitution: las implementaciones son intercambiables.
   - **I**nterface Segregation: interfaces pequeñas y específicas.
   - **D**ependency Inversion: depender de abstracciones, no de implementaciones concretas.

7. **Documentar decisiones no obvias.** Si se elige un patrón (Event Sourcing, CQRS, Hexagonal, etc.), explicar por qué es adecuado para este caso y qué alternativas se descartaron.

8. **Revisar con el usuario.** La arquitectura es una decisión de equipo. Presentar el diseño, recoger feedback e iterar antes de implementar.

## Criterios de éxito

- El diseño incluye al menos un diagrama de componentes y un diagrama de secuencia en Mermaid.
- Cada componente tiene su responsabilidad documentada.
- Los contratos entre módulos están definidos con tipos y manejo de errores.
- Las decisiones de diseño están justificadas, no son arbitrarias.
- El usuario ha validado la arquitectura propuesta.
