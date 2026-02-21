---
description: "Planificacion de releases: changelog, versionado semantico, notas y calendario"
---

# Planificacion de releases

El usuario quiere preparar una release del proyecto. Este skill guia el proceso completo desde la definicion de la version hasta la publicacion, asegurando que el changelog, las notas de release y la documentacion estan al dia.

## Contexto

Una release bien planificada no es solo un `git tag`. Requiere revisar que se incluye, comunicar los cambios a los usuarios y garantizar que la version sigue un esquema coherente. Este skill sistematiza ese proceso para que ninguna release salga sin changelog, sin notas o con una version incoherente.

## Protocolo

### Fase 1: Inventario de cambios (devops-engineer)

1. Listar todos los commits desde la ultima release (`git log --oneline <last-tag>..HEAD`).
2. Clasificar los cambios por tipo: feat, fix, refactor, docs, test, chore.
3. Identificar breaking changes que requieran bump de version major.
4. Verificar que todos los cambios tienen tests asociados.

**Artefacto:** listado clasificado de cambios.

### Fase 2: Versionado semantico

Determinar la nueva version segun semver (MAJOR.MINOR.PATCH):

| Tipo de cambio | Bump |
|----------------|------|
| Breaking change en API publica | MAJOR |
| Nueva funcionalidad retrocompatible | MINOR |
| Correccion de bug | PATCH |
| Solo docs, tests, refactor interno | PATCH (o ninguno si no hay cambios funcionales) |

Si hay dudas, consultar al usuario antes de decidir.

### Fase 3: Changelog (tech-writer)

Generar o actualizar el fichero CHANGELOG.md con formato Keep a Changelog:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Anadido
- Descripcion del cambio (#PR o commit)

### Cambiado
- Descripcion del cambio

### Corregido
- Descripcion del bug corregido

### Eliminado
- Funcionalidad o API eliminada (si aplica)
```

### Fase 4: Notas de release

Redactar las notas de release para GitHub/GitLab:

1. Titulo: version + nombre descriptivo si procede.
2. Resumen de 2-3 frases con los cambios mas relevantes.
3. Lista detallada de cambios (del changelog).
4. Instrucciones de actualizacion si hay breaking changes.
5. Agradecimientos a contribuidores si los hay.

### Fase 5: Publicacion (devops-engineer)

1. Actualizar la version en los ficheros del proyecto (package.json, plugin.json, etc.).
2. Crear el commit de release.
3. Crear el tag con `git tag vX.Y.Z`.
4. Publicar la release en GitHub con `gh release create`.
5. Verificar que la release aparece correctamente.

**Artefacto:** release publicada con changelog y notas.
