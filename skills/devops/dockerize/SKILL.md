---
name: dockerize
description: "Usar para generar Dockerfile optimizado"
---

# Generar Dockerfile optimizado

## Resumen

Este skill genera un Dockerfile siguiendo las mejores prácticas de la industria: multi-stage builds para reducir el tamaño de la imagen final, ejecución con usuario no-root para seguridad, capas optimizadas para aprovechar la caché y health checks para la orquestación.

Un buen Dockerfile no es solo "que funcione", sino que sea seguro, rápido de construir, pequeño y mantenible.

## Proceso

1. **Detectar el stack del proyecto.** Identificar el lenguaje, framework y runtime necesarios para determinar la imagen base adecuada:

   - Node.js: `node:XX-alpine` o `node:XX-slim`.
   - Python: `python:XX-slim` o `python:XX-alpine`.
   - Rust: multi-stage con `rust:XX` para build y `debian:XX-slim` o `gcr.io/distroless` para runtime.
   - Go: multi-stage con `golang:XX` para build y `scratch` o `gcr.io/distroless` para runtime.

2. **Diseñar multi-stage build.** Separar la fase de construcción de la de ejecución:

   ```dockerfile
   # Fase de build: incluye herramientas de compilación
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build

   # Fase de runtime: solo lo necesario para ejecutar
   FROM node:20-alpine AS runtime
   WORKDIR /app
   COPY --from=builder /app/dist ./dist
   COPY --from=builder /app/node_modules ./node_modules
   ```

3. **Optimizar el orden de capas para caché.** Las capas que cambian menos van primero:

   - Primero: ficheros de dependencias (package.json, requirements.txt, Cargo.toml).
   - Segundo: instalación de dependencias.
   - Tercero: copia del código fuente.
   - Cuarto: build.

   Esto asegura que un cambio en el código no invalida la caché de dependencias.

4. **Configurar usuario no-root.** Nunca ejecutar la aplicación como root dentro del contenedor:

   ```dockerfile
   RUN addgroup --system app && adduser --system --ingroup app app
   USER app
   ```

5. **Añadir health check.** Permitir al orquestador (Docker Compose, Kubernetes) verificar que la aplicación está sana:

   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:3000/health || exit 1
   ```

6. **Generar .dockerignore.** Excluir todo lo que no es necesario en la imagen:

   ```
   node_modules
   .git
   .env
   *.md
   tests/
   .github/
   ```

7. **Configurar variables de entorno.** Usar `ENV` para valores por defecto y documentar qué variables se deben pasar en runtime con `ARG` o `-e`.

8. **Verificar la imagen resultante.** Comprobar el tamaño final, que no incluye herramientas de build innecesarias y que arranca correctamente.

## Criterios de éxito

- El Dockerfile usa multi-stage build.
- La imagen base es mínima (alpine, slim o distroless).
- La aplicación se ejecuta con usuario no-root.
- Las capas están ordenadas para maximizar el uso de caché.
- Hay un health check configurado.
- Existe un .dockerignore que excluye ficheros innecesarios.
- La imagen final no incluye herramientas de build, tests ni código fuente innecesario.
