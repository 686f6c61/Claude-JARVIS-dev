---
name: tdd-cycle
description: "Usar siempre antes de implementar código. Ciclo rojo-verde-refactor estricto."
---

# Ciclo TDD (Test-Driven Development)

## Resumen

Este skill implementa el ciclo rojo-verde-refactor de TDD de forma estricta. La regla fundamental es que no se escribe ni una línea de código de producción sin un test que falle primero. Esto no es una sugerencia, es un HARD-GATE: si no hay test fallando, no se escribe implementación.

El TDD no es solo una técnica de testing, es una técnica de diseño. Escribir el test primero obliga a pensar en la interfaz pública antes que en la implementación, lo que produce código más limpio y con menor acoplamiento.

## Proceso

### Paso 1: Rojo - escribir un test que falle

- Escribir un único test que describa el comportamiento esperado.
- El test debe ser específico: probar UN aspecto del comportamiento, no varios.
- Nombrar el test de forma descriptiva: `deberia_devolver_error_cuando_email_es_invalido`, no `test1`.
- El test debe fallar por la razón correcta (el código no existe o no implementa el comportamiento), no por un error de sintaxis.

### Paso 2: Ejecutar y verificar que falla

- HARD-GATE: ejecutar el test y confirmar que falla.
- Verificar que el mensaje de error es el esperado. Si el test falla por una razón distinta a la esperada, corregir el test antes de continuar.
- Este paso no se puede saltar. Un test que pasa sin implementación significa que el test no está probando nada útil.

### Paso 3: Verde - implementación mínima

- Escribir el mínimo código necesario para que el test pase.
- "Mínimo" significa literalmente lo mínimo. Si el test espera que una función devuelva `true`, devolver `true` directamente es válido en este paso.
- No anticipar requisitos futuros. No añadir lógica que ningún test pide.
- No preocuparse por la elegancia del código en este paso.

### Paso 4: Ejecutar y verificar que pasa

- Ejecutar todos los tests (no solo el nuevo) y verificar que pasan.
- Si algún test existente se rompe, corregir la implementación sin cambiar los tests existentes (salvo que haya un test mal escrito).
- HARD-GATE: no avanzar hasta que todos los tests estén en verde.

### Paso 5: Refactorizar

- Ahora, con la red de seguridad de los tests, mejorar el código.
- Eliminar duplicación, mejorar nombres, extraer funciones, simplificar condicionales.
- Ejecutar los tests después de cada cambio de refactoring para asegurar que no se rompe nada.
- La refactorización no cambia comportamiento, solo estructura.

### Paso 6: Commit atómico

- Hacer commit del test y la implementación juntos. El commit debe ser atómico: si se revierte, el proyecto sigue en un estado consistente.
- Formato del commit: `feat: [descripción]` o `test: [descripción]` según corresponda.
- Volver al paso 1 con el siguiente comportamiento a implementar.

## Criterios de éxito

- No existe código de producción sin un test correspondiente que lo valide.
- Cada test se ha visto fallar antes de escribir la implementación.
- Los tests son independientes entre sí (no dependen de orden de ejecución ni de estado compartido).
- El refactoring se ha realizado con todos los tests en verde.
- Los commits son atómicos y cada uno deja el proyecto en estado funcional.
