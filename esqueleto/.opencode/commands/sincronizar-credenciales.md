---
description: Sincroniza credenciales profesionales (Credly + Google Skills Boost) y consolida data/credenciales/
---

Sincroniza el perfil de credenciales usando el servidor MCP `identidad`:

1. Ejecuta `identidad_credly_sincronizar` → insignias de Credly
2. Ejecuta `identidad_skillsboost_sincronizar` → insignias de Google Skills
3. Ejecuta `identidad_consolidar` → fusión deduplicada en `data/credenciales/consolidado.json`

Al finalizar, resume:
- Credenciales nuevas desde la última sincronización (si existía consolidado previo)
- Qué credenciales refuerzan la narrativa Cloud Support / Junior DevOps
- Qué credenciales NO están siendo aprovechadas en el CV actual
$ARGUMENTS
