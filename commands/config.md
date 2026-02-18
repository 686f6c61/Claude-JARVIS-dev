---
description: "Configura Alfred Dev: autonomía, stack, compliance y personalidad"
---

# Configuración de Alfred Dev

Lee el fichero `.claude/alfred-dev.local.md` si existe. Si no existe, créalo con la configuración por defecto.

Presenta al usuario la configuración actual organizada en secciones:

1. **Autonomía por fase** (interactivo/semi-autónomo/autónomo): producto, arquitectura, desarrollo, seguridad, calidad, documentación, devops
2. **Proyecto** (detectado o manual): nombre, lenguaje, framework, runtime, gestor de paquetes, base de datos, ORM
3. **Compliance**: RGPD, NIS2, CRA, sector, jurisdicción
4. **Integraciones**: CI, contenedores, registro, hosting, monitoring
5. **Personalidad**: nivel de sarcasmo (1-5), celebrar victorias, insultar malas prácticas

Usa AskUserQuestion para preguntar qué sección quiere modificar. Después de cada cambio, actualiza el fichero .local.md.

Si el proyecto no tiene configuración y hay ficheros en el directorio actual, ejecuta detección automática de stack y presenta los resultados al usuario para confirmar.
