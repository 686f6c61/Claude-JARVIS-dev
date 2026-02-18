---
name: write-adr
description: "Usar para documentar decisiones arquitectónicas como ADR"
---

# Escribir ADR (Architecture Decision Record)

## Resumen

Este skill genera un registro de decisión arquitectónica (ADR) siguiendo un formato estandarizado. Los ADR capturan no solo qué se decidió, sino por qué y qué alternativas se descartaron. Son la memoria institucional del proyecto: cuando dentro de seis meses alguien pregunte "por qué usamos X en vez de Y", el ADR tiene la respuesta.

Cada ADR es un fichero independiente, numerado secuencialmente, que se guarda en `docs/adr/`. Una vez aceptado, un ADR no se modifica; si la decisión cambia, se crea uno nuevo que lo sustituye.

## Proceso

1. **Identificar la decisión a documentar.** Un ADR se escribe cuando hay una decisión arquitectónica significativa: elección de tecnología, patrón de diseño, estructura de datos, estrategia de despliegue, etc. No documentar decisiones triviales.

2. **Obtener el siguiente número secuencial.** Listar los ADR existentes en `docs/adr/` y asignar el siguiente número (formato `NNN`, por ejemplo `001`, `002`, `015`).

3. **Redactar el ADR con la siguiente estructura:**

   - **Título:** `NNN - Descripción breve de la decisión`. Ejemplo: `003 - Usar PostgreSQL como base de datos principal`.
   - **Estado:** uno de `propuesto`, `aceptado`, `sustituido por [NNN]`, `rechazado`.
   - **Fecha:** cuándo se tomó la decisión.
   - **Contexto:** qué situación o problema motiva esta decisión. Incluir restricciones técnicas, de negocio o de equipo que influyen.
   - **Opciones evaluadas:** mínimo 3 alternativas, cada una con:
     - Descripción breve.
     - Ventajas.
     - Desventajas.
     - Riesgos.
   - **Decisión:** qué opción se elige y un párrafo explicando el razonamiento.
   - **Consecuencias:** divididas en positivas y negativas. Ser honesto con los compromisos que se asumen.

4. **Utilizar la plantilla base.** Si existe `templates/adr.md`, usarla como punto de partida para mantener consistencia entre ADRs del proyecto.

5. **Guardar el fichero.** Nombre: `docs/adr/NNN-titulo-en-kebab-case.md`. Ejemplo: `docs/adr/003-usar-postgresql.md`.

6. **Actualizar el índice si existe.** Si hay un fichero índice de ADRs (como `docs/adr/README.md` o `docs/adr/index.md`), añadir la nueva entrada.

7. **Revisar con el usuario.** El ADR es un registro de decisión consensuada. No se da por final hasta que el usuario lo aprueba.

## Criterios de éxito

- El ADR sigue la estructura estándar: título, estado, contexto, opciones, decisión, consecuencias.
- Se han evaluado al menos 3 alternativas con ventajas y desventajas documentadas.
- El contexto explica el "por qué" de la decisión, no solo el "qué".
- Las consecuencias son honestas e incluyen los compromisos asumidos.
- El fichero está guardado en `docs/adr/` con el formato de numeración correcto.
- El usuario ha aprobado el ADR.
