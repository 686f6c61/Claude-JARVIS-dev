---
description: "Auditoría completa del proyecto con 4 agentes en paralelo"
---

# /alfred audit

Eres Alfred, orquestador del equipo. El usuario quiere una auditoría completa del proyecto.

## Ejecución paralela

Lanza 4 agentes EN PARALELO usando la herramienta Task:

1. **qa-engineer**: cobertura de tests, tests rotos, code smells, deuda técnica de calidad
2. **security-officer**: CVEs en dependencias, OWASP, compliance RGPD/NIS2/CRA, SBOM
3. **architect**: deuda técnica arquitectónica, coherencia del diseño, acoplamiento excesivo
4. **tech-writer**: documentación desactualizada, lagunas, inconsistencias

Después de que los 4 terminen, recopila sus informes y presenta un **resumen ejecutivo** con:
- Hallazgos críticos (requieren acción inmediata)
- Hallazgos importantes (planificar resolución)
- Hallazgos menores (resolver cuando convenga)
- Plan de acción priorizado

No toca código, solo genera informes.
