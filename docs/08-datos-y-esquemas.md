# 8. Datos y esquemas

`data/` es el estado del sistema. Todo lo que el agente aprende vive aquí, en
JSON legible y versionado en git. El principio: **si el agente lo afirma, está en
`data/`**.

## 8.1 Mapa de `data/`

| Carpeta | Contiene | Quién escribe |
|---|---|---|
| `data/audit/` | Inventario de stack real desde GitHub | `tools/github_audit/audit.py` |
| `data/credenciales/` | Credly, Skills Boost y el consolidado | MCP `identidad` |
| `data/perfil/` | Entrevista, plan de brechas, notas de práctica | `reclutador-mentor`, tú |
| `data/vacantes/pendientes/` | Vacantes sin decidir y sus carpetas de análisis | MCP `empleo`, `analista-fit` |
| `data/vacantes/aprobadas/` | Vacantes que decidiste trabajar | MCP `empleo` |
| `data/vacantes/descartadas/` | Vacantes rechazadas (contexto histórico) | MCP `empleo` |
| `data/mercado/` | Requisitos agregados por frecuencia | `tools/mercado/agregar.py` |

```
data/
├── audit/
│   ├── stack_inventory.json    # fuente de verdad del stack
│   └── informe_github.md       # versión legible
├── credenciales/
│   ├── credly.json
│   ├── skillsboost.json
│   └── consolidado.json
├── perfil/
│   ├── entrevista-reclutador.md
│   └── plan-brechas.md
├── vacantes/
│   ├── pendientes/<id>.json
│   ├── aprobadas/<id>.json
│   ├── aprobadas/<id>/analisis.md      # cuando ya se analizó
│   └── descartadas/<id>.json
└── mercado/
    ├── requisitos_agregados.json
    └── reporte-AAAA-MM.md
```

`<id>` es estable y se deriva de la URL: `"<portal>-" + sha1(url)[:8]`. Por eso
la deduplicación entre corridas funciona sin base de datos.

## 8.2 Vacante (`data/vacantes/<estado>/<id>.json`)

```json
{
  "id": "remotive-1f90c3e2",
  "portal": "remotive",
  "titulo": "Support Engineer (Cloud)",
  "empresa": "Acme",
  "url": "https://remotive.com/remote-jobs/support/«...»",
  "ubicacion": "Worldwide",
  "modalidad": "remoto",
  "region_hint": "mundial",
  "salario": { "texto": "USD 1.500-2.000/mes", "min": 1500.0, "max": 2000.0, "moneda": "USD" },
  "publicada": "2026-10-20T00:00:00+00:00",
  "capturada": "2026-10-21T14:05:00+00:00",
  "tags": ["cloud", "support"],
  "resumen": "Primeros 400 caracteres del anuncio...",
  "descripcion_md": "Texto completo del anuncio, ya sin HTML.",
  "estado": "pendiente"
}
```

| Campo | Notas |
|---|---|
| `modalidad` | `remoto`, `híbrido`, `presencial` o vacío, inferido del anuncio |
| `region_hint` | `colombia`, `latam`, `mexico`, `espana` o `mundial` |
| `salario` | Los portales suelen dar solo texto; `min`/`max` quedan `null` si no se pueden parsear |
| `publicada` | Normalizada a ISO; los RSS traen RFC 2822 y se convierten |
| `estado` | `pendiente`, `aprobada` o `descartada`; refleja la carpeta |
| `descripcion_md` | Presente desde la búsqueda; `detalle` la refresca si faltaba |

Cuando `analista-fit` termina, **añade** un campo al mismo JSON:

```json
"fit": { "score": 72, "veredicto": "postular", "analisis": "data/vacantes/aprobadas/remotive-1f90c3e2/analisis.md" }
```

El `analisis.md` sigue el formato de la skill `analisis-fit`: requisitos
extraídos, scoring por componente (60/25/10/5), evidencia citada, brechas con
plan y veredicto razonado. Es la pieza que permite auditar por qué una vacante se
analizó como se analizó.

## 8.3 Inventario de stack (`data/audit/stack_inventory.json`)

```json
{
  "generado_en": "2026-10-21T13:00:00+00:00",
  "usuario": "«tu-usuario»",
  "total_repos": 12,
  "repos": [
    {
      "nombre": "mi-proyecto",
      "url": "https://github.com/«tu-usuario»/mi-proyecto",
      "descripcion": "«...»",
      "homepage": "",
      "privado": false,
      "fork": false,
      "archivado": false,
      "ultimo_push": "2026-09-30T10:00:00Z",
      "estrellas": 2,
      "lenguaje_principal": "Python",
      "lenguajes_bytes": { "Python": 45231, "Dockerfile": 812 },
      "topics": ["cloud", "automation"],
      "manifiestos": ["requirements.txt", "Dockerfile"],
      "stack": { "datos": ["Python", "Docker", "Streamlit"], "lenguajes": ["Python"] },
      "readme": {
        "existe": true,
        "caracteres": 1840,
        "describe_problema": true,
        "tiene_demo_o_capturas": false,
        "tiene_instrucciones": true,
        "menciona_arquitectura": true
      }
    }
  ],
  "agregado": {
    "skills_por_frecuencia": { "Python": 9, "Docker": 4, "Terraform": 1 },
    "cloud_providers": ["AWS"],
    "repos_con_iac": ["mi-proyecto"],
    "repos_con_cicd": ["otro-repo"],
    "repos_con_contenedores": ["mi-proyecto"],
    "repos_sin_readme": []
  }
}
```

El `stack.datos` es lo que el agente puede citar como evidencia en un análisis de
fit. Todo lo que no esté ahí, ni en las credenciales, ni confirmado en la
entrevista, no entra al CV.

`agregado.repos_sin_readme` es tu lista de deberes para la imagen pública: cada
repo sin README es una tecnología que tienes pero que nadie puede ver.

## 8.4 Credenciales (`data/credenciales/`)

Tres archivos con la misma forma final:

```
credly.json       ← volcado de la API de Credly
skillsboost.json  ← scraping del perfil de Google Skills
consolidado.json  ← fusión deduplicada de los dos anteriores
```

```json
{
  "actualizado": "2026-10-21T13:10:00+00:00",
  "usuario": "«tu-usuario»",
  "total": 14,
  "credenciales": [
    {
      "nombre": "AWS Cloud Practitioner",
      "emisor": "Amazon Web Services",
      "emitida": "2026-05-10",
      "skills": ["Cloud", "AWS"],
      "url": "https://www.credly.com/badges/«...»",
      "fuentes": ["credly", "skillsboost"]
    }
  ]
}
```

`consolidar` deduplica por nombre en minúsculas y sin caracteres no
alfanumericos — no por URL ni por emisor. Un badge presente en las dos fuentes
queda como una credencial con `fuentes: ["credly", "skillsboost"]`. Si cambias
alguna insignia en Credly, vuelve a correr `/sincronizar-credenciales`; el
consolidado se regenera.

## 8.5 Mercado (`data/mercado/requisitos_agregados.json`)

```json
{
  "generado": "2026-10-21T13:20:00+00:00",
  "vacantes_analizadas": 34,
  "por_portal": { "getonboard": 12, "remotive": 9, "linkedin": 7, "greenhouse": 6 },
  "modalidades": { "remoto": 30, "híbrido": 4 },
  "idiomas_publicacion": { "es": 14, "en": 20 },
  "senioridad": { "junior": 11, "mid": 15, "senior": 8 },
  "ingles_niveles": { "B2": 6, "C1": 3 },
  "salario_usd_mes": { "min": 800, "max": 3500, "mediana": 1600, "muestras": 12 },
  "requisitos_por_frecuencia": {
    "Docker/Contenedores": { "vacantes": 21, "porcentaje": 61.8 },
    "Linux": { "vacantes": 19, "porcentaje": 55.9 }
  },
  "brechas_vs_mi_evidencia": ["Kubernetes", "Terraform/IaC"],
  "detalle_por_vacante": [
    { "id": "remotive-1f90c3e2", "requisitos": ["Linux", "Docker", "Inglés"] }
  ]
}
```

Los conteos son **por vacante**, no menciones. Un requisito que aparece tres
veces en el mismo anuncio cuenta una sola vez. Esto es lo que hace comparable la
frecuencia entre vacantes de distinta extensión.

`brechas_vs_mi_evidencia` solo mira requisitos frecuentes (≥20 % de las vacantes
analizadas) que no estén cubiertos por el inventario, las credenciales o el
conjunto `MI_EVIDENCIA_EXTRA` de `tools/mercado/agregar.py`.

`reporte-AAAA-MM.md` es la misma información en prosa, un archivo por mes.

## 8.6 Perfil (`data/perfil/`)

| Archivo | Qué guarda |
|---|---|
| `entrevista-reclutador.md` | Salida de `/entrevista-cv`: hechos confirmados, datos por confirmar y decisiones de narrativa |
| `plan-brechas.md` | Máximo tres frentes activos de cierre de brechas, cada uno con señal de cierre |
| `inventario-habilidades-*.md` | Notas de apoyo que generes (formularios, práctica, bootcamps) |

No hay esquema JSON aquí a propósito: es texto que tú y el agente leen y
reescriben. Mantenerlo en Markdown estructurado (encabezados y listas) es
suficiente.

## 8.7 Convenciones de escritura

- **Codificación UTF-8 sin BOM.** El agente lee con `encoding="utf-8"` explícito.
- **JSON con `ensure_ascii=False, indent=2`.** Que un acento no se vuelva
  `\u00e9` y que el diff en git sea revisable.
- **Fechas ISO 8601 con zona.** `2026-10-21T13:20:00+00:00`.
- **Nada de campos calculados en la fuente.** El score de fit se agrega al
  analizar, no al guardar la vacante.
- **Un archivo por vacante.** El nombre del archivo es el `id`; moverlo de carpeta
  es cambiar de estado.

## 8.8 Qué se versiona

`.gitignore` del workspace:

```gitignore
tools/.venv/
rendercv/rendercv-env/
rendercv/build/
__pycache__/
*.pyc
.firecrawl/
tools/mcp_identidad/.session/
.DS_Store
*.log
```

Se versionan `data/` completo, `rendercv/src/`, `rendercv/tailored/` y
`rendercv/versions/`. No se versionan los venvs, los previews temporales ni las
sesiones de navegador.

Dos consecuencias útiles de versionar `data/`:

1. Dentro de un año puedes responder "¿por qué descarté esa vacante?" con
   `git log`.
2. Si el agente propone algo sin evidencia, `git diff` sobre `data/` lo delata.

## 8.9 Migrar el esquema

Si agregas un campo a las vacantes (por ejemplo `idioma_publicacion`), hazlo en
`tools/mcp_empleo/adapters/_comun.normalizar()` para que aplique a los seis
portales a la vez. No parchees los JSON existentes a mano: los archivos viejos
sin el campo deben seguir funcionando, y los consumidores deben leerlo con
`v.get("campo")` en lugar de `v["campo"]`.
