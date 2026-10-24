---
description: Agrega los requisitos de todas las vacantes y genera el reporte de mercado por frecuencia
---

Ejecuta el agregado determinista de mercado:

```
tools/.venv/Scripts/python.exe tools/mercado/agregar.py
```

Luego lee `data/mercado/reporte-<mes>.md` y presenta:
1. Top 10 requisitos del mercado con porcentaje
2. Brechas frecuentes vs mi evidencia (lo que debo cerrar)
3. Distribución de senioridad, idiomas y salario
4. 2-3 recomendaciones accionables para el backlog de proyectos de
   `rendercv/CONTEXTO_CARRERA.md` basadas en las brechas
$ARGUMENTS
