---
description: Actualiza el CV base (rendercv/src/cv) con la evidencia nueva del inventario, credenciales y mercado — propone cambios para tu aprobación
---

Trabaja sobre el CV base en `rendercv/src/cv/` con aprobación previa:

1. Lee `rendercv/src/cv/<CANDIDATO>.es.yaml` y `rendercv/src/cv/<CANDIDATO>.en.yaml`
2. Lee las fuentes de evidencia:
   - `data/audit/stack_inventory.json` (stack real por repos)
   - `data/credenciales/consolidado.json` (credenciales verificables)
   - `data/mercado/requisitos_agregados.json` (lo que pide el mercado)
   - `rendercv/CONTEXTO_CARRERA.md` (reglas y brechas)
3. Propón UNA LISTA de cambios concretos al CV (es y en, consistentes):
   - Credenciales nuevas que agregar a `certificaciones_y_cursos` (solo las que
     estén en el consolidado, con fecha y emisor reales)
   - Habilidades a reordenar/reescribir según lo que pide el mercado
   - Proyectos a reordenar según la narrativa <ROL_OBJETIVO>
   - El headline si aplica
4. Muestra el diff propuesto y ESPERA mi aprobación. No edits nada hasta que
   confirme.
5. Solo tras mi OK: aplica los cambios, corre
   `tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py preview` y
   muéstrame los PDFs. El release (`renderizar.py release --version vX.Y.Z`) lo
   decido yo.
$ARGUMENTS
