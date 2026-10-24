---
description: Ejecuta la auditoría de repos GitHub y actualiza el inventario de stack
agent: auditor-github
subtask: true
---

Ejecuta la auditoría completa de GitHub:

```
tools/.venv/Scripts/python.exe tools/github_audit/audit.py --salida data/audit
```

(Sin `--usuario` audita la cuenta autenticada en `gh`. Si quieres auditar otra,
agrega `--usuario <login>`.)

Luego lee `data/audit/stack_inventory.json` y `rendercv/CONTEXTO_CARRERA.md` y
presenta:
1. Stack confirmado vs declarado en el CV (coincidencias y contradicciones)
2. Los 3 repos más relevantes para la narrativa Cloud Support / Junior DevOps
3. Mejoras rápidas de perfil (READMEs faltantes o débiles, topics, descripciones)
$ARGUMENTS
