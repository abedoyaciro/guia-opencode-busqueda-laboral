---
name: analisis-fit
description: Rúbrica de scoring de vacantes (0-100), taxonomía de requisitos, formato del análisis individual y del reporte de brechas para el perfil Cloud Support/Junior DevOps
---

# Análisis de fit de vacantes

## Insumos (leer SIEMPRE antes de analizar)

1. `data/vacantes/pendientes|aprobadas/<id>.json` — la vacante + `descripcion_md`
2. `data/audit/stack_inventory.json` — skills con evidencia real en repos
3. `data/credenciales/consolidado.json` — credenciales verificables
4. `rendercv/CONTEXTO_CARRERA.md` — reglas: NUNCA inventar; hechos vs hipótesis

## Rúbrica de scoring (0-100)

| Componente | Peso | Cómo puntuar |
|---|---|---|
| Obligatorios cubiertos | 60 | fracción de requisitos excluyentes con evidencia × 60 |
| Deseables cubiertos | 25 | fracción de deseables con evidencia × 25 |
| Idioma | 10 | requiere B2/C1 y el candidato tiene B1 → 3 pts; no excluyente → 10 pts |
| Senioridad y modalidad | 5 | junior/entry-remoto-LatAm → 5; senior/lead → 0 |

Veredictos y probabilidad estimada (siempre presentada como estimación, no
promesa; depende de competencia, volumen de postulantes y filtros ATS):

| Score | Veredicto | Probabilidad estimada |
|---|---|---|
| ≥70 | postular | alta (~55-75%) de pasar screening inicial |
| 50-69 | postular con plan de preparación | media (~30-50%) |
| <50 | no postular (registrar para el mercado) | baja (<25%) |

## Formato de `analisis.md` (en data/vacantes/aprobadas/<id>/)

```markdown
# Análisis de fit — <título> (<empresa>)
Portal: <portal> | <url> | analizado: <fecha>

## Requisitos extraídos
- Obligatorios: [lista con los excluyentes marcados]
- Deseables: [lista]
- Idiomas: [ej: "inglés B2 excluyente" o "no especifica"]

## Scoring
- Obligatorios: X/Y → NN pts
- Deseables: X/Y → NN pts
- Idioma: → N pts
- Senioridad/modalidad: → N pts
- **TOTAL: NN/100 → <veredicto>**

## Evidencia en mi perfil
[requisito ↔ evidencia concreta: repo (de stack_inventory), credencial (de
consolidado), experiencia del CV, o "SIN EVIDENCIA"]

## Brechas y plan
[requisito faltante → acción: proyecto del backlog / curso / descartar]

## Veredicto y razones
```

## Reglas

- Cada afirmación de evidencia debe citar su fuente (repo, credencial, CV).
- Si un requisito no tiene evidencia, se marca como brecha — jamás se inventa.
- Actualizar el JSON de la vacante: `"fit": {"score": NN, "veredicto": "...", "analisis": "<ruta analisis.md>"}`.
- Los requisitos extraídos alimentan el agregado: `tools/mercado/agregar.py`.
