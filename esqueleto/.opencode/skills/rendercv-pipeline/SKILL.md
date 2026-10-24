---
name: rendercv-pipeline
description: Cómo generar y versionar CVs con RenderCV en este workspace — reglas de tailoring honesto, flujo preview→release, estructura de variantes por vacante
---

# Pipeline RenderCV (Windows)

## Comandos (vía orquestador Python, no make)

```
tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py preview
tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py vacante --dir <carpeta> --idioma es --design harvard
tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py custom --cv <yaml> --design <yaml> --locale <yaml> --out <dir>
tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py release --version v2.0.0
```

- `preview`: 4 PDFs del CV base en `rendercv/build/preview/{es,en}-{harvard,er}/`
- `vacante`: renderiza `rendercv/tailored/<carpeta>/cv.<idioma>.yaml` →
  `rendercv/tailored/<carpeta>/output/<CANDIDATO>-<carpeta>.pdf`
- `release`: versiona las 4 variantes con **TODOS los artefactos** (pdf, md,
  html, typ, png) en `rendercv/versions/<version>/<variante>/` + `manifest.yaml`
  + `versions/latest.txt`. El `.md` es el formato recomendado para que los
  agentes lean el CV sin gastar tokens en PDFs. No hace git commit/tag (decisión
  del usuario).
- Diseños: `harvard` | `engineeringresumes`. Idiomas: `es` | `en`.
- El `make release VERSION=vX.Y.Z` del Makefile queda solo para Git Bash/WSL.

## Estructura de una variante por vacante

```
rendercv/tailored/<empresa>-<rol>/
├── cv.es.yaml          # copia del base con cambios de énfasis
├── vacante.ref.json    # trazabilidad: id, url, estado de aprobación
├── notas-fit.md        # qué se cambió, por qué, y brechas detectadas
└── output/             # PDF (+PNG) generado
```

## Qué SE PUEDE cambiar en el tailoring

- Reordenar secciones y entradas (lo más relevante primero para esa vacante)
- Reescribir `headline` y `perfil_profesional` con el vocabulario de la vacante
  **sin agregar hechos nuevos**
- Seleccionar 3-4 proyectos más afines (puedes omitir proyectos irrelevantes)
- Reescribir `label`/`details` de habilidades agrupando por lo que pide la vacante
- Recortar secciones de bajo valor (p. ej. intereses) para ganar espacio

## Qué está PROHIBIDO (regla de `CONTEXTO_CARRERA.md`)

- Inventar experiencia, métricas, certificaciones o tecnologías sin evidencia
  en `data/audit/stack_inventory.json`, `data/credenciales/consolidado.json` o el CV actual
- Cambiar fechas, institución, contacto o cualquier dato duro
- Ocultar brechas: si la vacante pide algo que no tienes, va a `notas-fit.md`

## Flujo de aprobación (humano en el bucle)

1. La vacante debe estar **aprobada** por el usuario (o ser demo explícita)
2. El agente genera la variante + notas-fit y la PRESENTA para revisión
3. El usuario aprueba el CV → recién ahí es utilizable para postular
4. Release del CV base: solo con aprobación explícita

## Idioma de la variante

- Vacante en español → `cv.es.yaml` (default)
- Vacante en inglés → `cv.en.yaml` **solo si** el CV en inglés está alineado con
  el español. Si no lo está, propón primero la alineación al usuario.
