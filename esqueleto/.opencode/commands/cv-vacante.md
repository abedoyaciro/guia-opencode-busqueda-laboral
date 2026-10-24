---
description: Genera un CV personalizado para una vacante aprobada (RenderCV tailored) — requiere id de vacante
agent: cv-tailor
subtask: true
---

Genera la variante de CV para la vacante: $1

Pasos:
1. Busca la vacante por id en `data/vacantes/aprobadas/` o `pendientes/`
   (si está en pendientes y el usuario te pidió esta variante, muévela a
   aprobadas con `empleo_marcar`).
2. Sigue la skill `rendercv-pipeline`: crea `rendercv/tailored/<empresa>-<rol>/`
   con `cv.<idioma>.yaml`, `vacante.ref.json` y `notas-fit.md`.
3. Renderiza con `tools/rendercv/renderizar.py vacante ...`
4. Reporta: PDF generado, cambios principales, brechas no cubiertas, y
   recordatorio de que la aprobación final del CV es del usuario.
