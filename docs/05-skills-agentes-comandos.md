# 5. Skills, agentes y comandos

Tres mecanismos distintos que se confunden con facilidad:

| Mecanismo | Qué es | Cuándo se carga | Dónde vive |
|---|---|---|---|
| **Skill** | Documento de conocimiento y criterios | Cuando el agente decide que la tarea encaja con su `description` | `.opencode/skills/<nombre>/SKILL.md` |
| **Agente** | Rol con su propio prompt, temperatura y permisos | Al invocarlo, o como agente primario de una sesión | `.opencode/agents/<nombre>.md` |
| **Comando** | Plantilla de prompt con argumentos | Cuando escribes `/nombre` | `.opencode/commands/<nombre>.md` |

Regla mental: la **skill** aporta criterio, el **agente** aporta el rol y los
permisos, el **comando** aporta el atajo.

## 5.1 Skills

Anatomía mínima:

```markdown
---
name: rendercv-pipeline
description: Cómo generar y versionar CVs con RenderCV en este workspace — reglas de tailoring honesto, flujo preview→release
---

# Pipeline RenderCV (Windows)

## Comandos
...
```

- El frontmatter solo necesita `name` y `description`.
- La `description` es lo que el agente lee para decidir si la carga. Escribe ahí
  el "cuándo", no solo el "qué".
- El cuerpo se carga entero solo cuando la skill se usa: mantén las skills
  específicas y sin relleno.

Las de este sistema:

| Skill | Aporta |
|---|---|
| `analisis-fit` | Rúbrica de scoring 0-100, umbrales de veredicto, formato exacto de `analisis.md` |
| `auditoria-github` | Interpretación del inventario y qué hacer con READMEs débiles |
| `mercado-laboral` | Portales, vocabulario de búsqueda, filtro de seniority, estrategia junior |
| `rendercv-pipeline` | Qué se puede y qué no se puede cambiar en el tailoring, flujo de aprobación |

Además de las del proyecto, OpenCode carga skills de `~/.config/opencode/skills/`.
En este entorno hay cuatro globales que sirven de apoyo: `firecrawl` (navegación
y scraping), `playwright-skill` (automatización de navegador), `stop-slop`
(limpieza de redacción) y `grill-me` (interrogatorio para pensar decisiones).

### Cómo escribir una skill que se use

1. **Una tarea, un archivo.** Si la skill cubre dos cosas, se parten.
2. **Criterios numéricos, no adjetivos.** "Score ≥70 → postular" funciona;
   "evalúa bien el fit" no.
3. **Formato de salida explícito.** Si esperas un `analisis.md` con secciones
   fijas, ponlo en un bloque de código dentro de la skill.
4. **Reglas negativas claras.** Lo prohibido suele ser más importante que lo
   permitido: "jamás inventar métricas", "no tocar `rendercv/src`".
5. **Rutas reales.** Cita los archivos exactos que la skill necesita.

## 5.2 Agentes

Frontmatter de un agente de este repo:

```yaml
---
description: Analiza el fit de una vacante aprobada contra el inventario real y las credenciales
mode: subagent
temperature: 0.2
permission:
  bash:
    "*": deny
    "tools/.venv/Scripts/python.exe tools/mercado/*": allow
  skill:
    "*": allow
---
```

| Campo | Para qué |
|---|---|
| `description` | Cuándo delegarle trabajo; es lo que ve el agente principal |
| `mode` | `subagent` (lo invoca otro agente o un comando), `primary` o `all` |
| `temperature` | 0.1-0.2 para extracción y auditoría, 0.3-0.4 para redacción y entrevistas |
| `permission` | Endurece los permisos del proyecto; un agente nunca debe poder más que su host |
| `model` | Opcional: fija un modelo distinto para ese rol |

Los cinco agentes:

| Agente | Modo | Temperatura | Hace |
|---|---|---|---|
| `scout-vacantes` | subagent | 0.2 | Busca vacantes con el MCP `empleo` y las deja en pendientes. Sin permisos de edición ni bash |
| `auditor-github` | subagent | 0.1 | Ejecuta `audit.py` y reporta stack real, contradicciones con el CV y READMEs débiles |
| `analista-fit` | subagent | 0.2 | Análisis de fit de una vacante aprobada, con scoring y brechas |
| `cv-tailor` | subagent | 0.3 | Genera la variante de CV y la presenta para aprobación |
| `reclutador-mentor` | all | 0.4 | Entrevista para completar el CV y mentoría del plan de brechas. Único con `question: allow` |

El endurecimiento importa. `scout-vacantes` tiene `edit: deny` y `bash: deny`
porque su única vía de escritura es el MCP, que ya decide dónde guardar.
`analista-fit` solo puede ejecutar `tools/mercado/*`. `cv-tailor` puede editar
(crea YAML) pero solo ejecuta `tools/rendercv/*`.

## 5.3 Comandos

```markdown
---
description: Análisis de fit completo de una vacante (scoring + brechas + veredicto)
agent: analista-fit
subtask: true
---

Analiza la vacante indicada y produce el análisis de fit completo.

Vacante: $1
```

| Campo | Efecto |
|---|---|
| `agent` | Ejecuta el comando con ese agente en lugar del principal |
| `subtask: true` | Lo corre como subtarea, sin reemplazar la sesión en curso |
| `$1`, `$2` | Argumentos posicionales de la invocación |
| `$ARGUMENTS` | Todos los argumentos, útil en comandos abiertos |

Los diez comandos:

| Comando | Arg | Agente | Resultado |
|---|---|---|---|
| `/buscar-vacantes` | — | scout-vacantes | Guarda vacantes nuevas en pendientes |
| `/revisar-vacantes` | — | — | Presenta pendientes de 5 en 5 y aplica tus decisiones |
| `/agregar-vacante` | `url [notas]` | — | Ingresa una vacante que encontraste tú |
| `/analizar-vacante` | `id` | analista-fit | `analisis.md` con score, brechas y veredicto |
| `/cv-vacante` | `id` | cv-tailor | Variante de CV en PDF para esa vacante |
| `/cv-general` | — | — | Propone cambios al CV base y espera tu OK |
| `/auditar-github` | — | auditor-github | Actualiza el inventario de stack |
| `/sincronizar-credenciales` | — | — | Credly + Google Skills → consolidado |
| `/reporte-mercado` | — | — | Agregado de requisitos y brechas |
| `/entrevista-cv` | — | reclutador-mentor | Entrevista por bloques y actualización del CV |

## 5.4 Qué usar para cada intención

| Quieres... | Usa |
|---|---|
| Traer vacantes nuevas | `/buscar-vacantes` (o pídelo en lenguaje natural: "busca vacantes junior de soporte cloud") |
| Decidir sobre lo acumulado | `/revisar-vacantes` |
| Saber si vale la pena postular | `/analizar-vacante <id>` |
| Un CV ajustado a esa vacante | `/cv-vacante <id>` |
| Mejorar el CV base | `/cv-general` |
| Saber qué evidencia tienes | `/auditar-github` |
| Saber qué pide el mercado | `/reporte-mercado` |
| Completar huecos del CV | `/entrevista-cv` |
| Actualizar certificaciones | `/sincronizar-credenciales` |

## 5.5 Añadir tus propias piezas

**Una skill nueva**: crea `.opencode/skills/<nombre>/SKILL.md` con frontmatter
`name` y `description`, y cita las rutas que necesite. Si el agente no la usa
cuando debería, el problema casi siempre está en la `description`.

**Un agente nuevo**: copia uno existente y ajusta `description`, `temperature` y
`permission`. Empieza restrictivo: es más fácil relajar permisos que recuperarse
de un `git push` no deseado.

**Un comando nuevo**: plantilla corta que diga qué hacer y con qué agente. Si el
comando necesita más de 10 líneas de instrucciones, esa lógica pertenece a una
skill, y el comando solo la invoca.
