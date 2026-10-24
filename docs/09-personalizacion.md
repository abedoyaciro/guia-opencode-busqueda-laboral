# 9. Personalización para tu perfil

El esqueleto trae placeholders y ejemplos neutros. Esta es la lista de lo que
debes cambiar, en orden, y qué pasa si lo dejas como está.

## 9.1 Checklist de placeholders

| Archivo | Qué reemplazar | Si lo dejas |
|---|---|---|
| `opencode.json` | `CREDLY_USER`, `SKILLSBOOST_PROFILE_URL` | El MCP `identidad` no sincroniza nada |
| `AGENTS.md` | `<TU_ROL_OBJETIVO_PRINCIPAL>`, `<TU_ROL_OBJETIVO_SECUNDARIO>`, `<TU_SISTEMA_OPERATIVO>` | El agente trabaja con una narrativa que no es la tuya |
| `rendercv/CONTEXTO_CARRERA.md` | Todos los `<...>` | El tailoring no tiene contra qué validar |
| `rendercv/src/cv/` | Renombrar a `<CANDIDATO>.<idioma>.yaml` y editar el contenido | El PDF sale con datos de ejemplo |
| `tools/rendercv/renderizar.py` | La constante `CANDIDATO` | `preview` falla: busca el archivo con el nombre viejo |
| `.opencode/skills/analisis-fit/SKILL.md` | El perfil objetivo de la `description` | El agente puntúa contra un rol que no es el tuyo |
| `.opencode/skills/mercado-laboral/SKILL.md` | Vocabulario y portales | Búsqueda con términos que no son los del mercado que quieres |
| `tools/mercado/agregar.py` | `TAXONOMIA` y `MI_EVIDENCIA_EXTRA` | El reporte cuenta requisitos que no te importan y marca brechas falsas |

Tras reemplazar, ejecuta:

```powershell
pwsh -File guia-busqueda-laboral\scripts\verificar.ps1 -Raiz C:\ruta\busqueda-laboral
```

La sección 7 de la verificación te lista los placeholders que quedan.

## 9.2 Renombrar el CV

Tres pasos, siempre juntos:

```powershell
# 1. Renombrar los YAML (kebab-case, sin tildes)
Rename-Item rendercv\src\cv\nombre-apellido.es.yaml mi-nombre-apellido.es.yaml
Rename-Item rendercv\src\cv\nombre-apellido.en.yaml mi-nombre-apellido.en.yaml
```

```python
# 2. tools/rendercv/renderizar.py
CANDIDATO = "mi-nombre-apellido"
```

```powershell
# 3. Verificar
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py preview
```

`CANDIDATO` no es solo el nombre del YAML: es también el prefijo de los PDFs de
las variantes (`<CANDIDATO>-<carpeta>.pdf`). Si lo cambias después de generar
variantes, los PDFs viejos conservan el nombre viejo; no pasa nada, pero no los
busques con el patrón nuevo.

## 9.3 Escribir tu `CONTEXTO_CARRERA.md`

Es el archivo que impide que el agente invente. Escríbelo antes de pedir
cualquier CV, y trata cada línea como una afirmación auditable:

- **Perfil actual**: solo hechos verificables. "Practicante de soporte 6 meses en
  IBM" es un hecho. "Experto en cloud" no.
- **Evidencia técnica disponible**: solo lo que puedas respaldar con un repo, una
  credencial o una experiencia concreta. Si dudas, va en brechas, no aquí.
- **Posicionamiento**: cómo presentar el mismo perfil para dos roles distintos.
- **Brechas**: la lista que da sentido a `plan-brechas.md`.
- **Reglas para agentes**: no las dupliques con `AGENTS.md`; aquí van las
  específicas de carrera, allí las del workspace.

La estructura del esqueleto ya funciona. La regla es no rellenar un bloque si no
tienes el contenido: deja el placeholder antes que escribir algo que no puedes
probar.

## 9.4 Adaptar la taxonomía de requisitos

`TAXONOMIA` en `tools/mercado/agregar.py` es una lista de `(nombre_canónico,
regex)`. Define qué cuenta como requisito y con qué nombre se agrupa.

```python
TAXONOMIA = [
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b|\beks\b|\bgke\b|\baks\b"),
    ("Terraform/IaC", r"\bterraform\b|\binfrastructure as code\b|\bia[cC]\b"),
    ("Linux", r"\blinux\b|\bubuntu\b|\brhel\b|\bcentos\b|\bdebian\b"),
    # ... una entrada por requisito que te importe
]
```

Cómo ajustarla a tu búsqueda:

1. Deja los requisitos que aparecen en tus vacantes objetivo. Si buscas soporte
   cloud, `Linux`, `Docker`, `AWS`, `Redes` y `Soporte/Ticketing-ITIL` son
   obligatorios.
2. Elimina lo que no quieras ver en tu reporte. Cada entrada que dejas es ruido
   potencial en `requisitos_por_frecuencia`.
3. Cuida la especificidad: `\bgo\b` captura "Go" el lenguaje y "go" el verbo. Usa
   `\bgolang\b` o el nombre del ecosistema.
4. Agrupa sinónimos en el mismo canónico. `Kubernetes`/`k8s`/`EKS` deben contar
   juntos, no por separado.
5. Vuelve a correr `/reporte-mercado` y compara antes/después. Si los porcentajes
   se mueven de forma rara, una regex está capturando de más.

## 9.5 Declarar evidencia sin repo

`MI_EVIDENCIA_EXTRA` cubre lo que sabes hacer pero no está en ningún repositorio:
experiencia laboral, credenciales, cursos.

```python
MI_EVIDENCIA_EXTRA: set[str] = {"Linux", "Soporte/Ticketing-ITIL", "Redes"}
```

Los nombres deben coincidir **textualmente** con los canónicos de `TAXONOMIA`, o
la brecha seguirá apareciendo. Si no coincide, no hay aviso: simplemente el
script no lo reconoce.

La alternativa correcta para evidencia que sí es pública es un repo con README:
en el momento en que la GitHub Action lo detecte, entra a `stack_inventory.json` y
ya no necesitas declararla a mano.

## 9.6 Vocabulario de búsqueda

El scout hace cuatro búsquedas. Ese texto vive en
`.opencode/commands/buscar-vacantes.md` y en la skill `mercado-laboral`. Los
términos genéricos traen ruido; los específicos traen volumen bajo. Combina:

- Rol + nivel: `support engineer junior`, `devops junior`, `cloud support`.
- Siglas del stack que sí tienes: `aws linux support`, `docker kubernetes junior`.
- Términos que aparecen en las vacantes que quieres: `technical support`,
  `site reliability`, `platform engineer junior`.

Después de un par de corridas sabrás qué términos producen vacantes aprobables.
Lo que importa no es cuántas guardas, sino cuántas apruebas.

## 9.7 Ajustar la rúbrica de scoring

`analisis-fit` puntúa 60/25/10/5 (obligatorios/deseables/idioma/senioridad). Si tu
realidad es distinta, cambia los pesos en la skill y los umbrales:

- Si el idioma es excluyente en tu mercado, súbele el peso.
- Si tu problema es el nivel, dale más peso a senioridad.
- Ajusta los cortes de veredicto si 70 es demasiado optimista para tu volumen.

Los pesos deben sumar 100. Cualquier cambio aquí se refleja en los análisis
futuros, no en los ya escritos.

## 9.8 Añadir portales

El procedimiento técnico está en
[03. MCP § 3.5](03-mcp.md#35-añadir-un-portal-nuevo). Además:

- Documenta la limitación del portal en la skill `mercado-laboral` para que el
  scout no lo use como si fuera una API robusta.
- Si el portal exige JavaScript, el adaptador de LinkedIn es la plantilla: usa
  `playwright` con límites de peticiones, no `requests`.
- Si el portal da descripciones largas y limpias, la búsqueda ya puede incluir
  `descripcion_md` y el análisis de fit mejora sin pasos extra.

## 9.9 Tu narrativa en los agentes y comandos

Los archivos en `.opencode/agents/` y `.opencode/commands/` son plantillas. Busca
las referencias al rol objetivo y ajústalas:

```powershell
Select-String -Path .opencode\agents\*.md,.opencode\commands\*.md -Pattern 'Cloud Support|Junior DevOps|Cloud|DevOps'
```

Cada coincidencia es una instrucción que el agente seguirá al pie de la letra. Si
tu narrativa es distinta, cámbialas o añade tu propio rol. El agente no adivina:
hace lo que dicen sus instrucciones.

## 9.10 Qué NO personalizar a la ligera

- **Las reglas del workspace** (`AGENTS.md` § Reglas inquebrantables): relajarlas
  es la vía rápida a un CV con tecnología que no puedes defender en entrevista.
- **El bloque `permission`**: pasar `git push` o `gh repo edit` a `allow` elimina la
  aprobación humana en los cambios públicos.
- **El plugin de secretos**: quitarlo no te da nada y te expone a que el agente
  lea un `.env` en un barrido de repos.
- **La separación de venvs**: instalar RenderCV dentro de `tools/.venv` suele
  romper alguna dependencia de `mcp` o `playwright` por conflicto de versiones.
