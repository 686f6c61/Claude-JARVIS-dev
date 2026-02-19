# Agentes opcionales y sistema de configurabilidad

Fecha: 2026-02-19

## Contexto

Alfred Dev tiene 8 agentes fijos (nucleo) que cubren el ciclo de vida de desarrollo estandar. Sin embargo, muchos proyectos necesitan roles adicionales que no son universales: no todos los proyectos tienen base de datos, frontend, landing publica o necesidades de rendimiento.

El objetivo es crear un catalogo de agentes predefinidos opcionales que el usuario pueda activar segun las necesidades de su proyecto. Alfred detectara automaticamente que agentes pueden ser utiles (descubrimiento contextual) y se los sugerira.

## Decision de arquitectura

Se elige el **enfoque de ficheros sueltos con convencion de directorio** (Enfoque A) por las siguientes razones:

- Trabaja con el sistema de plugins de Claude Code en lugar de contra el.
- Los agentes se registran en plugin.json como cualquier otro. La activacion es logica (Alfred los invoca o no segun la config), no fisica.
- No requiere modificar plugin.json en runtime ni reiniciar Claude Code.
- Cada agente opcional tiene su propia identidad: nombre, color, modelo, prompt, personalidad y frases.
- Maxima simplicidad: los ficheros .md ya son el formato nativo del sistema de agentes.

## Catalogo de agentes opcionales

| Agente | Modelo | Cuando lo sugiere Alfred | Skills propias |
|--------|--------|--------------------------|----------------|
| data-engineer | sonnet | Proyecto con BD/ORM | schema-design, migration-plan, query-optimization |
| ux-reviewer | sonnet | Proyecto con frontend | accessibility-audit, usability-heuristics, flow-review |
| performance-engineer | sonnet | Proyecto grande o con requisitos de rendimiento | profiling, benchmark, bundle-size |
| github-manager | sonnet | Cualquier proyecto con remote Git | repo-setup, pr-workflow, release, issue-templates |
| seo-specialist | sonnet | Proyecto web con contenido publico | meta-tags, structured-data, lighthouse-audit |
| copywriter | sonnet | Textos publicos: landing, emails, onboarding | copy-review, cta-writing, tone-guide |

## Skills nuevas para agentes existentes

| Skill | Agente | Proposito |
|-------|--------|-----------|
| docs/project-docs | tech-writer | Documentacion completa en docs/ para dar contexto absoluto |
| docs/glossary | product-owner | Corpus linguistico / glosario de terminos del proyecto |
| docs/readme-review | tech-writer | Auditoria y mejora del README |
| docs/onboarding-guide | tech-writer | Guia para nuevos desarrolladores |
| docs/migration-guide | tech-writer | Guia de migracion entre versiones |
| calidad/sonarqube | qa-engineer | SonarQube con Docker, analisis y mejoras |
| calidad/spelling-check | qa-engineer | Verificacion ortografica (tildes prioritarias) |
| seguridad/dependency-update | security-officer | Revision y actualizacion de dependencias |

## Estructura de directorios

```
agents/
  (8 agentes nucleo existentes)
  optional/
    data-engineer.md
    ux-reviewer.md
    performance-engineer.md
    github-manager.md
    seo-specialist.md
    copywriter.md

skills/
  (7 carpetas existentes, se amplian documentacion/, calidad/, seguridad/)
  datos/          (nueva: schema-design, migration-plan, query-optimization)
  ux/             (nueva: accessibility-audit, usability-heuristics, flow-review)
  rendimiento/    (nueva: profiling, benchmark, bundle-size)
  github/         (nueva: repo-setup, pr-workflow, release, issue-templates)
  seo/            (nueva: meta-tags, structured-data, lighthouse-audit)
  marketing/      (nueva: copy-review, cta-writing, tone-guide)
```

## Configuracion del usuario

Nueva seccion `agentes_opcionales` en alfred-dev.local.md:

```yaml
agentes_opcionales:
  data-engineer: true
  ux-reviewer: false
  performance-engineer: false
  github-manager: true
  seo-specialist: true
  copywriter: false
```

Todos desactivados por defecto. Se activan con `/alfred config` o por descubrimiento contextual.

## Descubrimiento contextual

Funcion `suggest_optional_agents()` en config_loader.py que:

1. Analiza el stack del proyecto (ya existente).
2. Detecta presencia de BD/ORM, frontend, web publica, remote GitHub, tamano del proyecto.
3. Devuelve lista de agentes sugeridos con la razon.
4. Alfred presenta las sugerencias al usuario con AskUserQuestion.
5. Los seleccionados se guardan en alfred-dev.local.md.

## Hook de ortografia

Nuevo hook `spelling-guard.py` en PostToolUse para Write|Edit que verifica tildes en castellano usando una lista de palabras conocidas. Sin dependencias externas.

## Actualizacion de la landing

- Mostrar 14 agentes (8 nucleo + 6 opcionales) con indicacion visual.
- Actualizar contadores de stats.
- Explicar el sistema de agentes opcionales en la seccion de agentes.
- Actualizar FAQ con preguntas sobre agentes opcionales.
- Anadir skills nuevas al recuento.

## Plan de implementacion

### Fase 1: infraestructura (config_loader + personality)
1. Actualizar DEFAULT_CONFIG en config_loader.py con seccion agentes_opcionales
2. Anadir suggest_optional_agents() a config_loader.py
3. Anadir los 6 agentes opcionales a personality.py
4. Actualizar /alfred config para gestionar agentes opcionales

### Fase 2: agentes opcionales (6 ficheros .md)
5. Crear agents/optional/ con los 6 agentes
6. Actualizar plugin.json para registrarlos
7. Actualizar alfred.md para integrarlos en flujos segun config

### Fase 3: skills nuevas
8. Crear skills para agentes existentes (docs, calidad, seguridad)
9. Crear skills para agentes opcionales (datos, ux, rendimiento, github, seo, marketing)

### Fase 4: hook de ortografia
10. Crear hooks/spelling-guard.py
11. Registrar en hooks.json

### Fase 5: landing
12. Actualizar index.html con los nuevos agentes, skills, FAQ y contadores

### Fase 6: tests y verificacion
13. Tests para config_loader (agentes opcionales, sugerencias)
14. Tests para personality (nuevos agentes)
15. Verificacion de la landing
